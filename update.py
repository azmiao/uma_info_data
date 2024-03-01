import asyncio
import time

from spider import uma_spider
from utils import *


async def auto_update_info(current_attempts: int):
    if current_attempts >= exceed_attempt:
        logging.error(f'The maximum allowable error limit has been reached.')
        raise Exception(f'The maximum allowable error limit has been reached.')
    current_attempts += 1
    current_dir = os.path.join(dir_name, 'config_v2.json')

    # Create base file
    if not os.path.exists(current_dir):
        logging.info(f'> The configuration file for uma database does not exist. Starting to create it.')
        current_dir_tmp = current_dir
    else:
        logging.info(f'> The configuration file already exists and is starting to create a copy. '
                     f'Once completed, the original file will be overwritten.')
        current_dir_tmp = os.path.join(dir_name, 'config_tmp.json')
    with open(current_dir_tmp, 'w', encoding='UTF-8') as af:
        json.dump({}, af, indent=4, ensure_ascii=False)

    # Update data
    logging.info(f'> Starting automatic update of uma database.')
    try:
        except_uma = await uma_spider(current_dir_tmp)
        if not except_uma:
            logging.info(f'> The automatic update of uma\'s database has been completed, '
                         f'and the corresponding Chinese name has been updated.')
        else:
            logging.error(f'uma\'s database update encountered an issue while updating {except_uma}. '
                          f'The update will continue from that uma in 2 minutes')
            await asyncio.sleep(120)
            await auto_update_info(current_attempts)
            return
    except (IndexError, TypeError):
        logging.error('OCR_SPACE API response failed! Automatic updates will continue in 2 minutes')
        await asyncio.sleep(120)
        await auto_update_info(current_attempts)
        return
    except Exception as e:
        logging.error(f'The automatic update of uma\'s database failed and will continue in 2 minutes. Reason: {e}')
        await asyncio.sleep(120)
        await auto_update_info(current_attempts)
        return

    # Copy the cache file content to a real configuration file
    await replace_config(current_dir_tmp, current_dir)
    logging.info('Chinese name update completed! The task is over!')

    # Update upgrade time
    version_dir = os.path.join(dir_name, 'version.txt')
    current_timestamp = time.time()
    current_time = time.strftime('%Y-%m-%d %H:%M:%S %Z%z', time.localtime(current_timestamp))
    with open(version_dir, 'w', encoding='UTF-8') as f:
        f.write(str(current_time))


if __name__ == '__main__':
    # init async task
    logging.info(f'==== Auto update action start ====')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(auto_update_info(0))
    logging.info(f'==== Auto update action finished ====')
