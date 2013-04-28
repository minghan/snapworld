import os
import sys
import time
import json
import threading
import urlparse
import logging
import subprocess

import BaseHTTPServer
import SocketServer

bindir = os.environ["SNAPWBIN"]
workdir = os.environ["SNAPWEXEC"]
python = os.environ["PYTHON"]

sys.path.append(bindir)

import client
import config
import daemon

class Server(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def do_GET(self):
        #print "GET path", self.path
        parsed_path = urlparse.urlparse(self.path)
        message_parts = [
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_type=%s' % "host server",
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                'HEADERS RECEIVED:',
                ]
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        message = '\r\n'.join(message_parts)

        subpath = self.path.split("/")

        if self.path == "/prepare":

            # move qin to qact
            qinname = "snapw.%d/qin" % (self.pid)
            qactname = "snapw.%d/qact" % (self.pid)

            # rename an existing qact
            qactnewname = "none"
            if os.path.exists(qactname):
                t = time.time()
                s = time.strftime("%Y%m%d-%H%M%S", time.localtime(t))
                mus = "%06d" % (t*1000000 - int(t)*1000000)
                qactnewname = "%s-%s-%s" % (qactname, s, mus)
                os.rename(qactname, qactnewname)

            # get the number of active tasks, rename existing qin
            numtasks = 0
            if os.path.exists(qinname):
                os.rename(qinname, qactname)
                active = os.listdir(qactname)
                numtasks = len(active)

            # create new qin
            config.mkdir_p(qinname)
    
            logging.info("preparing next step: %s, %s, %s" % \
                    (qinname, qactname, qactnewname))

            # send ready to master
            client.ready(self.master, self.id, numtasks)

            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()
            return

        elif self.path == "/quit":
            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()

            # set the flag to terminate the server
            self.server.running = False
            self.server.self_dummy()
            return

        elif self.path == "/dummy":
            print "dummy request"

            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()
            return

        elif self.path == "/step":
    
            logging.info("execute next step")

            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()

            # TODO, implement null action,
            #   skip execution if there are no tasks to execute,
            #   qact does not exist

            # get the tasks to execute
            qactname = "snapw.%d/qact" % (self.pid)
            active = []
            if os.path.exists(qactname):
                active = os.listdir(qactname)

            logging.debug("active tasks %s" % (str(active)))

            self.qactname = qactname
            self.active = active
            # start a thread to execute the work tasks
            t = threading.Thread(target=Execute, args=(self, ))
            t.start()
            return

        elif self.path == "/config":
    
            logging.debug("get configuration")

            body = json.dumps(self.config)
            self.send_response(200)
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)

            return

        elif self.path == "/quit":
    
            logging.info("terminate execution")

            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()
            sys.exit(0)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

    def do_POST(self):
        #print "POST path", self.path
        parsed_path = urlparse.urlparse(self.path)
        message_parts = [
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_type=%s' % "host server",
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                'HEADERS RECEIVED:',
                ]
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        message = '\r\n'.join(message_parts)

        length = int(self.headers.get("Content-Length"))

        body = ""
        if length  and  length > 0:
            body = self.rfile.read(length)

        subpath = self.path.split("/")
        
        if subpath[1] == "msg":
            dst = subpath[2]
            src = subpath[3]

            dirname = "snapw.%d/qin/%s" % (self.pid, dst)
            config.mkdir_p(dirname)

            fname = "%s/%s" % (dirname, src)
            f,fnew = config.uniquefile(fname)
            f.write(body)
            f.close()
    
            logging.info("message %s length %d" % (fnew,  length))

            self.send_response(200)
            self.send_header('Content-Length', 0)
            self.end_headers()
            return

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        self.wfile.write('Path: %s\n' % self.path)

    def do_POST1(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        self.wfile.write('Path: %s\n' % self.path)
        self.wfile.write('Form data:\n')

        # Echo back information about what was posted in the form
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                self.wfile.write('\tUploaded %s as "%s" (%d bytes)\n' % \
                        (field, field_item.filename, file_len))
            else:
                # Regular form value
                self.wfile.write('\t%s=%s\n' % (field, form[field].value))
        return

    def log_message(self, format, *args):
        pass

class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                            BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

    def execute(self):
        while self.running:
            self.handle_request()

        print "exit"
        sys.exit(0)

    def self_dummy(self):
        haddr = "%s:%s" % (self.host, self.port)
        client.dummy(haddr)

def Execute(args):
    logging.info("Execute " + str(args.active) + "")
    tnow = time.time()
     
    if len(args.active) > 0:
        execdir = os.path.join(args.workdir, "snapw.%d/exec" % (args.pid))
        config.mkdir_p(execdir)
     
    def execute_single_task(task):     
        # get the executables
        bunch = "%s" % (task.split("-",1)[0])
        execlist = []
        try:
            execlist = args.config["bunch"][bunch]["exec"].split(",")
        except:
            pass
     
        for item in execlist:
            execpath = os.path.join(execdir, item)
            # check if the program exists and its mtime
            mtime = None
            try:
                stat = os.stat(execpath)
                mtime = int(stat.st_mtime)
            except:
                pass
     
            if not mtime  or  mtime < tnow:
                # the file does not exist or it is older than current time,
                #   contact the head task
     
                content = client.getexec(args.master,item,mtime)
                swc = "None"
                if content:
                    swc = str(len(content))
     
                logging.debug("Host received %s" % (swc))
                if content:
                    if len(content) > 0:
                        logging.debug("Host saving to %s" % (execpath))
                        f = open(execpath,"w")
                        f.write(content)
                        f.close()
       
                    os.utime(execpath,(tnow, tnow))
     
        prog = execlist[0]
        logging.debug("Task %s, exec %s" % (prog, execlist))
        progpath = os.path.join(execdir, prog)
     
        if not os.path.exists(progpath):
            logging.error("task %s not started, program %s not found" % (task, progpath))
            return
     
        taskdir = "snapw.%d/tasks/%s" % (args.pid, task)
        config.mkdir_p(taskdir)
     
        qdir = os.path.join(args.workdir, args.qactname, task)
        tdir = os.path.join(args.workdir, taskdir)
     
        logging.info("starting task %s, prog %s, workdir %s, qdir %s\n" % (task, prog, tdir, qdir))
             
        # get server information
        host = args.server.host
        port = args.server.port
     
        # construct a command line
        cmd = python + " %s -t %s -h %s:%d -q %s" % (
            progpath, task, host, port, qdir)
        logging.info("starting cmd %s" % (cmd))
     
        # start the work process
        p = subprocess.Popen(cmd.split(), cwd=tdir)
        return p
     
    # Dynamically check what the number of processors we have on each host
    # In any error, default to 1.
    try:
        max_tasks = os.sysconf('SC_NPROCESSORS_ONLN')
    except:
        max_tasks = 1
    logging.info("Running tasks with " + str(max_tasks) + "-way parallelism")
     
    # execute the tasks in a parallel fashion by running
    # at most max_tasks processes at any point.
    task_list = args.active[:]
    procs = []
    while True:
        while task_list and len(procs) < max_tasks:
            task = task_list.pop()
            procs.append(execute_single_task(task))
                
        for p in procs:
            # wait for the process to complete
            
            pid = p.pid
            logging.debug("polling %d" % pid)
            status = p.poll()
            if status is not None:
                logging.debug("finished %d" % pid)
                procs.remove(p)
 
        if not procs and not task_list:
            break
        else:
            time.sleep(1.0)
 
    # send done to master
    client.done(args.master, args.id)

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print "Usage: " + sys.argv[0] + " -d -i <id> -p <port> -m <host>:<port>"
        sys.exit(1)

    
    host = "0.0.0.0"
    port = None
    master = None

    daemon_mode = False
    index = 1
    while index < len(sys.argv):
        arg = sys.argv[index]
        if arg == "-i":
            index += 1
            id = sys.argv[index]
        elif arg == "-p":
            index += 1
            port = int(sys.argv[index])
        elif arg == "-m":
            index += 1
            master = sys.argv[index]
        elif arg == "-d":
            daemon_mode = True

        index += 1

    if port == None:
        print "Usage: " + sys.argv[0] + " -d -i <id> -p <port> -m <host>:<port>"
        sys.exit(1)

    if daemon_mode:
        # TODO(nkhadke): How to log this? Do we need to log this?
        print "daemon"
        retCode = daemon.createDaemon()

    os.chdir(workdir)
    pid = os.getpid()
    
    fname1 = "log-snapw-host-%d.txt" % (port)
    fname = "log-swhost-%d.txt" % (pid)

    fd = os.open(fname1, os.O_APPEND | os.O_WRONLY) # standard input (0)
    #flog = open(fname, "a") # standard input (0)

    # Duplicate standard input to standard output and standard error.
    os.dup2(0, 1)           # standard output (1)
    os.dup2(0, 2)           # standard error (2)

    # Set up logging
    logging.basicConfig(filename=fname, level=logging.DEBUG, format='[%(levelname)s] [%(asctime)s] [%(process)d] [%(filename)s] [%(funcName)s] %(message)s')

    server = ThreadedHTTPServer((host, port), Server)
    server.host = host
    server.port = port
    server.running = True

    handler = BaseHTTPServer.BaseHTTPRequestHandler
    handler.port = port
    handler.id = id
    handler.pid = os.getpid()
    handler.workdir = workdir
    handler.master = master

    if master != None:
        # get configuration from master
        sconf = client.config(master)
    
        dconf = json.loads(sconf)
        handler.config = dconf
    
        logging.debug("Config size: %d" % (len(sconf)))
        logging.debug(str(dconf))
            
        # send done to master
        client.done(master, id)

        # TODO time conflict. The master might already send 'step' request,
        #       before server_forever() is started, so 'step' might be lost.
        #       Delay done until the server is up and running.
        # check out Asynchronous Mixins example for SocketServer
        # Comment: the constructor might already activate the server,
        #       so there is no problem.
    
        logging.debug("Supervisor sent /done to master")

    logging.info("Starting host server pid %d, id %s, port %d with master %s\n" % (pid, id, port, master))
    
    server.execute()

