import re

from bs4 import BeautifulSoup

from chinesefy import get_cn_name
from detail_class import uma_from_dict, Uma, Adapt, uma_to_dict
from utils import *


# consistent with the result of using the "window.__ NUXT__.config" command through the browser console
async def get_nuxt_config() -> dict:
    logging.info('> Start getting nuxt config...')
    response = await async_request(f'https://{uma_domain}/character')
    soup = BeautifulSoup(response.text, 'lxml')
    soup_find = soup.find('script', text=re.compile(r'window\.__NUXT__\.config'))
    if soup_find is None:
        raise Exception('Cannot find nuxt_config in html!')
    find_text = soup_find.text
    strip_list = find_text.split(';')

    # json parse
    nuxt_config = {}
    for strip in strip_list:
        if 'window.__NUXT__.config' in strip:
            raw_config = strip.replace('window.__NUXT__.config=', '')
            # format json
            valid_json_data = re.sub(r'(?!https?)\b(\w+):', r'"\1":', raw_config)
            # special replace | difficult to add in re pattern
            valid_json_data = valid_json_data.replace('""cursor": pointer"', '"cursor: pointer"')
            nuxt_config = json.loads(valid_json_data)
    logging.info(f'nuxt config: {nuxt_config}')
    if not nuxt_config:
        raise Exception('Parse nuxt_config failed!')
    return nuxt_config


# get id list from character page
async def get_uma_id_list(nuxt_config: dict) -> list:
    logging.info('> Start getting uma id list...')
    micro_cms = nuxt_config.get('public', {}).get('microCMS', {})
    micro_key = micro_cms.get('apiKey', '')
    micro_domain = micro_cms.get('serviceDomain', '')
    default_headers['X-Microcms-Api-Key'] = micro_key

    # params
    params = [
        ('fields', 'id'),
        ('limit', 10000),
        ('offset', 0)
    ]
    # request
    response = await async_request(
        f'https://{micro_domain}.microcms.io/api/v1/character',
        headers=default_headers,
        params=params,
        timeout=600
    )
    response_json = dict(response.json())

    # get id list
    return [x.get('id', '') for x in response_json.get('contents', [])]


# get uma detail from character detail page
async def get_uma_detail(nuxt_config: dict, uma_id: str) -> Uma:
    micro_cms = nuxt_config.get('public', {}).get('microCMS', {})
    micro_key = micro_cms.get('apiKey', '')
    micro_domain = micro_cms.get('serviceDomain', '')
    default_headers['X-Microcms-Api-Key'] = micro_key

    # request
    response = await async_request(
        f'https://{micro_domain}.microcms.io/api/v1/character/{uma_id}',
        headers=default_headers,
        timeout=600
    )
    return uma_from_dict(json.loads(response.text))


async def uma_spider(current_dir):
    # result list
    uma_json_dict = {}
    # get micro_cms config
    nuxt_config = await get_nuxt_config()
    # get id list
    id_list = await get_uma_id_list(nuxt_config)
    logging.info(f'uma id list: {id_list}')
    # get uma detail
    uma_list = []
    logging.info(f'> Start getting detail info...')
    for uma_id in id_list:
        logging.info(f' - {uma_id}')
        uma_detail = await get_uma_detail(nuxt_config, uma_id)
        uma_list.append(uma_detail)
    logging.info(f'> Detail info query finished.')

    # file_dir | mkdir if not exist
    voice_dir = os.path.join(dir_name, 'voice_data')
    if not os.path.exists(voice_dir):
        logging.info('voice_data dir is not exist, we will create it.')
        os.mkdir(voice_dir)

    # add chinese's prop
    cn_uma_dict = await get_cn_name()
    for uma in uma_list:
        jp_name = uma.name
        uma_prop = cn_uma_dict.get(jp_name, {})
        # cn_name
        uma.cn_name = uma_prop.get('cn_name', '')
        # adapt
        uma.adapt = Adapt(
            uma_prop.get('grass', ''),
            uma_prop.get('mud', ''),
            uma_prop.get('short', ''),
            uma_prop.get('mile', ''),
            uma_prop.get('middle', ''),
            uma_prop.get('long', ''),
            uma_prop.get('run_away', ''),
            uma_prop.get('first', ''),
            uma_prop.get('center', ''),
            uma_prop.get('chase', ''),
        )
        # download voice
        await download_file(uma.voice.url, voice_dir, f'{uma.id}.mp3')
        # trans to json dict and save
        uma_json_dict[uma.id] = uma_to_dict(uma)

    # write into file
    logging.info(f'uma_json_dict: {uma_json_dict}')
    with open(current_dir, 'w', encoding='UTF-8') as af:
        json.dump(uma_json_dict, af, indent=4, ensure_ascii=False)
