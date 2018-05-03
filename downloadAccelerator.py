#!/usr/bin/env python

import requests
import sys
import argparse
import threading
import time

# {thread_id: "the response", ....}
responses = {}

def handleCommandLineOpts():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num-threads", help="the number of threads to use to download the url", type=int)
    parser.add_argument("url", help="the url to download")
    args = parser.parse_args()
    if args.num_threads is None:
        args.num_threads = 1
    return args.num_threads, args.url

def getContentLength(url):
    headers = {'Accept-Encoding': 'identity'}
    resp = requests.head(url, headers=headers)
    if 'Content-Length' in resp.headers:
        return int(resp.headers['Content-Length'])

def getFileName(url):
    lastSlash = url.rfind("/") + 1
    name = url[lastSlash:]
    if name == "":
        return "index.html"
    return name

class DownloaderThread(threading.Thread):
    """Get a range of bytes from a URL"""
    def __init__(self, t_id, url, start_ix, end_ix):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.t_id = t_id
        self.url = url
        self.start_ix = start_ix
        self.end_ix = end_ix

    def run(self):
        headers = {'Range': 'bytes=%s-%s' % (self.start_ix, self.end_ix), 'Accept-Encoding': 'identity',}
        chunk = requests.get(self.url, headers=headers)
        self.lock.acquire()
        try:
            responses[self.t_id] = chunk.content
        finally:
            self.lock.release()

if __name__ == "__main__":
    num_threads, url = handleCommandLineOpts()
    contentLength = getContentLength(url)
    # print "Url: %s\nnum_threads: %s\nContent-Length: %s" % (url, num_threads, contentLength)
    threadLength = contentLength // num_threads
    cur_ix = 0
    threads = []
    start_time = time.time()
    # Divide length by number of threads
    for i in range(num_threads):
        from_ix = cur_ix
        to_ix = cur_ix + threadLength
        if to_ix > contentLength:
            to_ix = contentLength
        # Start threads for each length
        t = DownloaderThread(i, url, from_ix, to_ix)
        t.start()
        threads.append(t)
        # print i, from_ix, "-", to_ix
        cur_ix = cur_ix + threadLength + 1

    # Join the threads & put it back in order
    for t in threads:
        t.join()

    # Save it
    filename = getFileName(url)
    with open(filename, "wb") as outFile:
        for i in range(num_threads):
            outFile.write(responses[i])

    # Output the info
    end_time = time.time()
    tot_time = end_time - start_time
    print url, num_threads, contentLength, tot_time