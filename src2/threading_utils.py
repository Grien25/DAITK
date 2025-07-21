import threading

def run_in_thread(target, args=(), callback=None):
    def wrapper():
        result = target(*args)
        if callback:
            callback(result)
    thread = threading.Thread(target=wrapper)
    thread.start()
    return thread 