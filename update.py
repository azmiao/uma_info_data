import json
import os
import asyncio
import logging
import argparse

from spider import uma_spider, get_cn, replace_config

logging.basicConfig(level=logging.INFO)
current_dir = os.path.join(os.path.dirname(__file__), 'config.json')

async def auto_update_info(APIKEY):
    if not os.path.exists(current_dir):
        logging.info(f'====马娘数据库配置文件不存在，正在开始创建====')
        data = {}
        with open(current_dir, 'w', encoding = 'UTF-8') as af:
            json.dump(data, af, indent=4, ensure_ascii=False)
        current_dir_tmp = current_dir
    else:
        logging.info(f'====马娘数据库配置文件已，正在开始创建副本，完成后会覆盖原文件====')
        data = {}
        current_dir_tmp = os.path.join(os.path.dirname(__file__), 'config_tmp.json')
        if not os.path.exists(current_dir_tmp):
            with open(current_dir_tmp, 'w', encoding = 'UTF-8') as af:
                json.dump(data, af, indent=4, ensure_ascii=False)
    logging.info(f'开始自动更新马娘数据库')
    try:
        except_uma = await uma_spider(current_dir_tmp, APIKEY)
        if not except_uma:
            msg = f'马娘数据库自动更新完成，开始更新对应中文名'
            logging.info(msg)
        else:
            msg = f'马娘数据库更新在更新{except_uma}时遇到问题，3分钟后将从该马娘开始继续更新'
            logging.error(msg)
            await asyncio.sleep(180)
            await auto_update_info()
            return
    except (IndexError, TypeError):
        logging.error('马娘数据 OCR_SPACE API响应失败！将在3分钟后继续自动更新')
        await asyncio.sleep(180)
        await auto_update_info()
        return
    except Exception as e:
        msg = f'马娘数据库自动更新失败，将在3分钟后继续自动更新，原因：{e}'
        logging.error(msg)
        await asyncio.sleep(180)
        await auto_update_info()
        return
    await get_cn(current_dir_tmp)
    await replace_config(current_dir_tmp, current_dir)
    logging.info('马娘数据库中文名更新完成！任务结束！')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-key', default=None)
    args = parser.parse_args()
    APIKEY = args.key
    loop = asyncio.get_event_loop()
    loop.run_until_complete(auto_update_info(APIKEY))