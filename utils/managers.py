from multiprocessing.managers import BaseManager

from utils.threads import ThreadAsync


async def add_func():
    BaseManager.register('getter', callable=ThreadAsync().async_thread)
    manager = BaseManager(address=('', 4444), authkey=b'111')
    server = manager.get_server()
    server.serve_forever()
