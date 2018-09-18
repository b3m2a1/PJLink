import threading
from .KernelLink import KernelLink
from .StdLink import StdLink
from .MathLinkExceptions import MathLinkException
from .MathLinkEnvironment import MathLinkEnvironment as Env
from collections import deque
from .HelperClasses import MPackage

class Reader:
    """
     The Reader is what listens for calls from Mathematica for the "installable Java" functionality
 of J/Link. When InstallJava[] is called, the Reader thread is started up. It either polls ml.ready()
 or blocks in ml.nextPacket() (this is the default), depending on settings controlled from Mathematica.
 Blocking will hang the whole JVM unless either
    - the JVM supports native threads
    - a yield function is used to call back into Java
 All windows JVMs support native threads, and they are available for all UNIX platforms (although
 you might have to get a recent one). Blocking will give the best performance, since it avoids the
 busy-wait associated with polling. On the Macintosh, native threads are not available, so we block
 and use a yielder. On UNIX, we poll in non-native threads VMs (it is the users responsibility inform
 J/Link that native threads are not supported by setting $NativeThreads = False before calling InstallJava[]).
 When blocking, the Reader thread owns the link's monitor, so computations that need to originate on
 another thread (typically the UI thread) cannot proceed. The kernel has to call jAllowUIComputations
 to cause the Reader to stop blocking and begin polling, which it does for the period during which
 UI computations are allowed. This period can be an extended time if DoModal[] is called, or it can
 be just a single computation (as allowed by ShareKernel[] or ServiceJava[]).

 Calls arrive in the form of CallPackets, and they are sent to the KernelLink's handleCallPacket() method.

    """

    def __init__(self, link, quit_on_link_end = True, is_main_link = False, always_poll = False):
        self.__link = link
        self.__quit_on_link_end = quit_on_link_end
        self.__stop_requested = False
        self.__thread = threading.Thread(target=self.run)
        self.__always_poll = always_poll
        self.__killer = threading.Event()

        # this is for a polling setup, mainly
        self.__eval_queue = deque([])
        self.__results_queue = deque([])
        self.__eval_number = 0
        self.__results_number = 0

        #  The Reader needs to operate slightly differently on the mainLink (JavaLink[]) than when used
        #  on the new preemptiveLink. Specifically, it never polls on the preemptiveLink because that
        #  link can never participate in DoModal[]. This variables distinguishes the two behaviors of this class.
        self.__is_main_link = is_main_link
        self.__sleep_interval = 2
        link._addMessageHandlerOn(self, "terminateMsgHandler")
        self.__started = False

        if isinstance(link, KernelLink):
            link._reader = self

    @property
    def link(self):
        return self.__link
    @property
    def quit_on_link_end(self):
        return self.__quit_on_link_end
    @property
    def stop_requested(self):
        return self.__stop_requested
    @property
    def thread(self):
        return self.__thread

    @classmethod
    def create_reader(cls, link, quit_on_link_end = True, always_poll = False, start = True):
        # startReader() and stopReader() allow advanced programmers to manage a Reader thread in their own programs,
        # if they desire. This can be tricky, and these methods are not formally documented for now (although they are public).
        # One reason to start a Reader thread is to allow scriptability of a Java application that was launched standalone.
        # Your program must then be able to handle requests arriving from the kernel at unexpected times. This means that you
        # need a component in your program that is able to read incoming packets all the time. That is what the Reader thread is.
        # You might also want to have your Java program and the front end share the kernel so that either can be used to initiate
        # computations. ShareKernel requires a Reader thread because it peppers the Java link with calls (for sleeping and for
        # jUIThreadWaiting[]).
        #
        # Users who call startReader() will probably want to set quitWhenLinkEnds=false (so the JVM does
        # not exit when the link or the Reader thread dies) and alwaysPoll=true. The main advantage of alwaysPoll is that by
        # forcing polling you make it possible to stop the Reader thread by simply calling stopReader(). It is not logically
        # required to force polling--as long as your program calls StdLink.requestTransaction() and synchronizes properly
        # on the link (as documented elsewhere), it should work with either polling or blocking.
        #
        # Once you call startReader(), your StdLink.requestTransaction() calls will block until the kernel gives them
        # permission to proceed (via ShareKernel, DoModal, or ServiceJava). So call ShareKernel or equivalent right after
        # you start the Reader. And don't forget that when the Reader is running, _every_ computation you send must be
        # guarded by StdLink.requestTransaction() and synchronized(ml), whether from the main thread or the UI thread.

        reader = cls(link, quit_on_link_end = quit_on_link_end, is_main_link = True, always_poll = always_poll)
        # We set StdLink to be the main link primarily for pre-5.1 kernels. For 5.1+ kernels there is a second UI link
        # that will be used for calls to M from the UI thread (unless we are in the modal state, in which case
        # the link we set here is used).

        link.Env.log("Starting!")

        if start:
            reader.__thread.start()
        StdLink.link = link
        StdLink.reader = reader

        return reader

    @property
    def started(self):
        return self.__started

    def evaluate(self, expr, wait=True):
        if self.__started:
            self.__eval_queue.append(expr)
            if wait:
                import time
                self.__eval_number += 1
                eval_num = self.__eval_number
                while eval_num > self.__results_number:
                    time.sleep(.05)
                return self.__results_queue.popleft()
        else:
            return self.__link.evaluate(expr, wait)

    def evaluateString(self, expr, wait=True):
        self.evaluate(MPackage.ToExpression(expr), wait)

    def stop_reader(self):
        # StopReader() will generally only be effective if you have called startReader() with alwaysPoll=true. Always call this
        # instead of (or at least before) stop() on the thread (unless you are about to exit the VM).
        # When Java is launched via InstallJava[] (the normal mode for "installable Java"), this method is not used--the
        # Reader thread dies when the link to the kernel is killed.
        self.__stop_requested = True
        StdLink.link = None
        return self

    def run(self): #should find a way to support yield with this to allow for a less-blocking run?
        import time

        loops_ago = 0
        self.__started = True
        try:
            while not self.__stop_requested:
                if len(self.__eval_queue) > 0:
                    try:
                        to_eval = self.__eval_queue.popleft()
                    except IndexError as e:
                        # import traceback as tb
                        # self.__link.Env.log(tb.format_exc())
                        pass
                    else:
                        ev_res = self.__link._evaluate(to_eval, wait = True)
                        self.__results_queue.append(ev_res)
                        self.__results_number += 1

                    continue

                if self.__killer.is_set():
                    self.__link.Env.log("Done!")
                    self.__stop_requested = True
                    break

                if self.__is_main_link and self.must_poll:
                    # Polling is much less efficient than blocking. It is used only in special circumstances (such as while the kernel is
                    # executing DoModal[], or after the kernel has called jAllowUIComputations[True]). It is also used on non-native threads
                    # UNIX JVMs (this use is controlled from Mathematica via jForcePolling).
                    is_ready = False
                    try:
                        is_ready = self.__link.ready
                        if not is_ready:
                            time.sleep(( self.__sleep_interval + min(loops_ago, 20) )/1000)
                    except:
                        pass

                    with self.__link._wrap(checkError=False, checkLink=False):
                        try:
                            self.__link._check_error(0)
                            if is_ready:
                                loops_ago = 0
                                pkt = self.__link._nextPacket()
                                self.__link._handlePacket(pkt)
                                self.__link._newPacket()
                        except MathLinkException as e:
                            # 11 is "other side closed link"; not sure why this succeeds clearError, but it does.
                            if e.no == 11 or not self.__link._clearError():
                                return None

                else:
                    # Use blocking style (dive right into MLNextPacket and block there). Much more efficient. Requires a native threads JVM
                    # or a yield function callback into Java; otherwise, all threads in the JVM will hang.
                    with self.__link._wrap(checkError=False, checkLink=False):
                        try:
                            self.__link.Env.log("Hitting nextPacket and blocking")
                            pkt = self.__link._nextPacket()
                            self.__link._handlePacket(pkt)
                            self.__link._newPacket()
                            must_poll = StdLink.must_poll
                        except MathLinkException as e:
                            # 11 is "other side closed link"; not sure why this succeeds clearError, but it does.
                            import traceback as tb
                            self.__link.Env.log(tb.format_exc())
                            if e.no == 11 or e.no == 1 or not self.__link._clearError():
                                return None
                            self.__link._newPacket()

        except Exception as e:
            import traceback as tb
            self.__link.Env.log(tb.format_exc())

        finally:
            # Get here on unrecoverable MathLinkException, ThreadDeath exception caused by "hard" aborts
            # from Mathematica (see KernelLinkImpl.msgHandler()), or other Error exceptions (except during invoke()).
            # TODO: For sake of JavaKernel, do I want to move the link-closing stuff up here before the quitWhenLinkEnds test?
            self.__link.Env.log("Bailing out of run")
            self.__started = False
            if self.__quit_on_link_end:
                self.__link.close()
                self.__link = None
                ui_link = StdLink.UI_link
                if ui_link is not None:
                    ui_link.close()
                    StdLink.UI_link = None
                StdLink.link = None

    def _terminateMessageHandler(self, msg, ignore):
        mname = Env.getMessageName(msg)
        if mname == "Terminate":
            # Will throw ThreadDeath exception, which triggers finally clause in run(), closing link and killing Java.
            self.__killer.set()
            self.__thread.join(0)

            # On some systems (Linux, perhaps all UNIX), if you are blocking in a read call, the stop() above will
            # have no effect. Something about being called from a native method, I suppose (the stop() works fine
            # if Java is busy with something other than blocking inside MathLink). For such cases, we set a yielder
            # that just returns true to make the read back out. Then the Reader thread stops.

            self.__link._setYieldFunctionOn(self, self._terminateYielder)
            self.__stop_requested = True

    def _terminateYielder(self):
        return True

    @property
    def must_poll(self):
        return self.__always_poll or StdLink.must_poll