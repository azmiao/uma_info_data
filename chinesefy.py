from bs4 import BeautifulSoup

from utils import *


# 获取马娘的适应性 | 和支援卡的适应性略有不同
async def get_com_uma(uma_dict):
    url = 'https://wiki.biligame.com/umamusume/赛马娘图鉴'
    res = await async_request(url, timeout=15)
    soup = BeautifulSoup(res.text, 'lxml')
    uma_list_tmp = soup.find_all('tr')
    uma_list = [x for x in uma_list_tmp if x.get('data-param1') in ['3', '2', '1']]
    for uma_info in uma_list:
        if uma_info.find_all('span', {'lang': 'ja'})[0].text == '[[测试/模板:赛马娘|]]':
            continue
        jp_name = uma_info.find_all('span', {'lang': 'ja'})[1].text
        if jp_name not in uma_dict:
            uma_dict[jp_name] = {
                'cn_name': uma_info.find_all('span', {'lang': 'ja'})[1].find('a').get('title').split('】')[-1]}
        com_list = uma_info.find_all('div', {'style': 'display:none'})
        i = 0
        for c_type in com_str:
            uma_dict[jp_name][c_type] = com_list[i].text.strip()
            i += 1
    return uma_dict


async def get_cn_name():
    uma_dict = {}
    url = 'https://wiki.biligame.com/umamusume/支援卡图鉴'
    res = await async_request(url, timeout=15)
    soup = BeautifulSoup(res.text, 'lxml')
    # 青春杯获取的适应性
    uma_list_tmp = soup.find_all('tr')
    uma_list = [x for x in uma_list_tmp if x.get('data-param1') in ['SSR', 'SR', 'R']]
    for uma_info in uma_list:
        jp_name = uma_info.find('div', {'style': 'position:relative;width:100px;margin:auto;'}) \
            .find('a').get('title').split('】')[-1]
        com_list = uma_info.find_all('td', {'class': 'visible-md visible-sm visible-lg'})
        if com_list[2].text.strip() == '团队':
            continue
        uma_dict[jp_name] = {}
        cn_name = com_list[0].text.strip()
        cn_name = '春' + cn_name if cn_name == '乌拉拉' else cn_name
        uma_dict[jp_name]['cn_name'] = cn_name
        i = 0
        for c_type in com_str:
            uma_dict[jp_name][c_type] = com_list[i + 4].text.strip()
            i += 1
    # 实际马娘适应性
    uma_dict = await get_com_uma(uma_dict)
    # 绿帽战神
    for c_type in com_str:
        uma_dict['駿川たづな'][c_type] = 'S'
    return uma_dict
