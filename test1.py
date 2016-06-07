import handlers
import aiomysql,asyncio
import orm
import logging;logging.basicConfig(level=logging.INFO)

def test(loop):
    yield from orm.create_pool(loop=loop,user='www-data',password='www-data',db='first')
    r=yield from handlers.api_post_users(email='12345678@123.com',name='micheal8',passwd='1111111111111111111111111111111111111111')
    body=r.body.decode('utf-8')
    logging.info(body)

loop=asyncio.get_event_loop()
loop.run_until_complete(test(loop))


loop.close
