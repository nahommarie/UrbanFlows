#Current working ssh client file

from twisted.conch.ssh import transport, connection, userauth, channel, common
from twisted.internet import defer, protocol, reactor
from twisted.python import log
import sys, getpass
log.startLogging(sys.stderr)

class ClientCommandTransport(transport.SSHClientTransport):
    def __init__(self, username, password, command):
        self.username = username
        self.password = password
        self.command = command

    def verifyHostKey(self, pubKey, fingerprint):
        # in a real app, you should verify that the fingerprint matches
        # the one you expected to get from this server
        return defer.succeed(True)

    def connectionSecure(self):
        self.requestService(
            PasswordAuth(self.username, self.password,
                         ClientConnection(self.command)))

class PasswordAuth(userauth.SSHUserAuthClient):
    def __init__(self, user, password, connection):
        userauth.SSHUserAuthClient.__init__(self, user, connection)
        self.password = password

    def getPassword(self, prompt=None):
        return defer.succeed(self.password)

class ClientConnection(connection.SSHConnection):
    def __init__(self, cmd, *args, **kwargs):
        connection.SSHConnection.__init__(self)
        self.command = cmd

    def serviceStarted(self):
        self.openChannel(CommandChannel(self.command, conn=self))

class CommandChannel(channel.SSHChannel):
    name = 'session'

    def __init__(self, command, *args, **kwargs):
        channel.SSHChannel.__init__(self, *args, **kwargs)
        self.command = command

    def channelOpen(self, data):
        self.conn.sendRequest(
            self, 'exec', common.NS(self.command), wantReply=True).addCallback(
            self._gotResponse)

    def _gotResponse(self, _):
        print "running _gotResponse"
        #self.conn.sendEOF(self)

    def _dataReceived(self, _, data):
        print "received: {0}".format(data)
        print data

    def closed(self):
        reactor.stop()

class ClientCommandFactory(protocol.ClientFactory):
    def __init__(self, username, password, command):
        self.username = username
        self.password = password
        self.command = command

    def buildProtocol(self, addr):
        protocol = ClientCommandTransport(
            self.username, self.password, self.command)
        return protocol

server = '18.111.53.136' #hostname that this file connects to
#server = '10.0.0.2'
command = 'python /home/pi/UrbanFlows/slavePi2/takepic.py'
#command = 'whoami'
#username = raw_input("Username: ")
username = 'pi'
password = 'raspberry'
#password = getpass.getpass("Password: ")
factory = ClientCommandFactory(username, password, command)
reactor.connectTCP(server, 2222, factory)
reactor.run()
