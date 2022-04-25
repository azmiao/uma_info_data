import json
import httpx
import logging
import re
import os
from PIL import Image

from chinesefy import get_cn_name

# 将缓存文件内容拷贝到真实的配置文件内
async def replace_config(current_dir_tmp, current_dir):
    with open(current_dir_tmp, 'r', encoding = 'UTF-8') as f:
        uma_data = json.load(f)
        f.close()
    with open(current_dir, 'w', encoding = 'UTF-8') as af:
        json.dump(uma_data, af, indent=4, ensure_ascii=False)

class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

async def uma_spider(current_dir, APIKEY):
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        uma_data = json.load(f)
        f.close()
    try:
        en_name = uma_data['current_chara']
    except:
        en_name = 'specialweek'
    if en_name == 'specialweek':
        uma_data = {}
    next_en_name = ''
    while(1):
        if next_en_name == 'specialweek':
            uma_data['current_chara'] = 'specialweek'
            with open(current_dir, 'w', encoding = 'UTF-8') as af:
                json.dump(uma_data, af, indent=4, ensure_ascii=False)
                af.close()
            break
        try:
            data, next_en_name, en_name = await get_info(en_name, APIKEY)
        except httpx._exceptions:
            return en_name
        uma_data['current_chara'] = en_name
        uma_data[en_name] = data
        logging.info(f'成功处理{en_name}的数据！')
        en_name = next_en_name
        with open(current_dir, 'w', encoding = 'UTF-8') as af:
            json.dump(uma_data, af, indent=4, ensure_ascii=False)
            af.close()
    return ''

# 拿到中文名字
async def get_cn(current_dir):
    uma_dict = await get_cn_name()
    with open(current_dir, 'r', encoding = 'UTF-8') as f:
        f_data = json.load(f)
        f.close()
    name_list = list(f_data.keys())
    name_list.remove('current_chara')
    for en_name in name_list:
        jp_name = f_data[en_name]['jp_name']
        try:
            cn_name = uma_dict[jp_name]['cn_name']
            if cn_name == '乌拉拉':
                cn_name = '春' + cn_name
        except:
            cn_name = ''
        try:
            grass = uma_dict[jp_name]['grass']
            mud = uma_dict[jp_name]['mud']
            short = uma_dict[jp_name]['short']
            mile = uma_dict[jp_name]['mile']
            middle = uma_dict[jp_name]['middle']
            long = uma_dict[jp_name]['long']
            run_away = uma_dict[jp_name]['run_away']
            first = uma_dict[jp_name]['first']
            center = uma_dict[jp_name]['center']
            chase = uma_dict[jp_name]['chase']
        except:
            grass, mud, short, mile, middle, long, run_away, first, center, chase = '', '', '', '', '', '', '', '', '', ''
        f_data[en_name]['cn_name'] = cn_name
        f_data[en_name]['grass'] = grass
        f_data[en_name]['mud'] = mud
        f_data[en_name]['short'] = short
        f_data[en_name]['mile'] = mile
        f_data[en_name]['middle'] = middle
        f_data[en_name]['long'] = long
        f_data[en_name]['run_away'] = run_away
        f_data[en_name]['first'] = first
        f_data[en_name]['center'] = center
        f_data[en_name]['chase'] = chase

    with open(current_dir, 'w', encoding = 'UTF-8') as af:
        json.dump(f_data, af, indent=4, ensure_ascii=False)
        af.close()

# 获取官网数据
async def get_info(en_name, APIKEY):
    url = f'https://umamusume.jp/app/wp-json/wp/v2/character?slug={en_name}'
    params = {
        'pragma': 'no-cache',
        'referer': f'https://umamusume.jp/character/detail/?name={en_name}'
    }
    uma_res = httpx.get(url, params = params, timeout = 10)
    uma_json = uma_res.json(object_hook=Dict)
    uma_data = uma_json[0]
    detail_img = uma_data['acf']['detail_img']['pc']
    cv, bir, height, weight, measurements = await download_ocr(en_name, detail_img, APIKEY)
    category = uma_data['acf']['category']['value']
    try:
        voice = uma_data['acf']['voice']
    except:
        voice = ''
    try:
        uniform_img = uma_data['acf']['chara_img'][0]['image']
    except:
        uniform_img =''
    try:
        winning_suit_img = uma_data['acf']['chara_img'][1]['image']
    except:
        winning_suit_img = ''
    try:
        original_img = uma_data['acf']['chara_img'][2]['image']
    except:
        original_img = ''
    data = {
        'id': uma_data['id'],
        'jp_name': uma_data['title']['rendered'],
        'category': category,
        'voice': voice,
        'uniform_img': uniform_img,
        'winning_suit_img': winning_suit_img,
        'original_img': original_img,
        'cv': cv,
        'bir': bir,
        'height': height,
        'weight': weight,
        'measurements': measurements,
        'sns_icon': uma_data['acf']['sns_icon'],
        'prev_en_name': uma_data['next']['slug'],
        'next_en_name': uma_data['prev']['slug']
    }
    return data, data['next_en_name'], en_name

# ocr识别
async def download_ocr(en_name, url, APIKEY):
    path = os.path.join(os.path.dirname(__file__), 'data/')
    if not os.path.exists(path):
        os.mkdir(path)
    response = httpx.get(url, timeout=10)
    resp_data = response.content
    current_dir = os.path.join(path, f'{en_name}.png')
    with open(current_dir, 'wb') as f:
        f.write(resp_data)
    # 调整分辨率
    img = Image.open(current_dir)
    imgSize = img.size
    if imgSize != (1292, 836):
        out = img.resize((1292, 836), Image.ANTIALIAS)
        out.save(current_dir)

    api = 'https://api.ocr.space/parse/image'
    data = {
        'apikey': APIKEY,
        'language': 'jpn',
        'filetype': 'PNG',
        'scale': True,
        'detectOrientation': False
    }
    with open(current_dir,'rb') as f:
        resp = httpx.post(api, files = {f'{en_name}.png': f}, data = data, timeout = 60)
        res_json = resp.json(object_hook=Dict)
    text = res_json['ParsedResults'][0]['ParsedText'].replace('\r\n', '')
    cv, bir, height, weight, measurements = '', '', '', '', ''
    text = str(text)
    cv_tmp = re.search(r'CV:(\S+)([0-9]+月)', text)
    cv = cv_tmp.group(1) if cv_tmp else cv
    # 修正ocr识别问题
    cv = cv.replace('0', 'o').replace('、', '').replace('小自唯', '小仓唯')
    bir_tmp = re.search(r'([0-9]+月[0-9]+日)', text)
    if bir_tmp:
        bir = bir_tmp.group(0) if bir_tmp else bir
        bir = bir.replace('月', '-').replace('日', '')
        bir_list = bir.split('-', 1)
        bir = '-'.join(str(int(bir_num, 10)) for bir_num in bir_list)
    height_tmp = re.search(r'([0-9][0-9][0-9])5', text)
    height_tmp_2 = re.search(r'([0-9][0-9][0-9])(c|C|。)m', text)
    height_tmp_3 = re.search(r'[0-9][0-9][0-9]', text)
    if height_tmp:
        height = height_tmp.group(1)
        weight_tmp = re.search(r'([0-9][0-9][0-9])5(\S*)(B[0-9][0-9])', text)
        weight = weight_tmp.group(2) if weight_tmp else weight
    elif height_tmp_2:
        height = height_tmp_2.group(1)
        weight_tmp = re.search(r'([0-9][0-9][0-9])(c|C|。)m(\S*)(B[0-9][0-9])', text)
        weight = weight_tmp.group(3) if weight_tmp else weight
    elif height_tmp_3:
        height = height_tmp_3.group(0)
        weight_tmp = re.search(r'([0-9][0-9][0-9])(\S*)(B[0-9][0-9])', text)
        weight = weight_tmp.group(2) if weight_tmp else weight
    else:
        height = height
        weight = weight
    measurements_tmp = re.search(r'(B[0-9]+・W[0-9]+・H[0-9]+)', text)
    measurements = measurements_tmp.group(0) if measurements_tmp else measurements
    # 这写ocr顺序有问题，正则匹配结果异常
    if en_name == 'currenchan':
        cv, weight = '篠原侑', 'ひ・み・つ'
    if en_name == 'marveloussunday':
        cv, bir, height, weight, measurements = '三宅麻理恵', '5-31', '145', 'マーベラス!', 'B87・W52・H77'
    if en_name == 'bikopegasus':
        cv, weight = '田中あいみ', '体重微増（いっぱい食べて大きくなる！）'
    if en_name == 'kitasanblack':
        cv, weight = '矢野妃菜喜', 'もりもり成長中!'
    if en_name == 'winningticket':
        cv = '渡部優衣'
    if en_name == 'fujikiseki':
        cv = '松井恵理子'
    return cv, bir, height, weight, measurements