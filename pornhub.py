from logging import root
import config
from requests_manage import RequestManager
from m3u8_downloader import M3U8Downloader
import re, json, html, os, time
import execjs           # pip install pyexecjs


class PornhubDownloader:

    def __init__(self, view_url = None, urls_txt = None):
        if view_url:
            self.download_one(view_url)
        elif urls_txt:
            self.download_some(urls_txt)
        

    def download_one(self, view_url):
        start_time = time.perf_counter()
        success = False

        video_id = re.search(r'viewkey=((ph)?[0-9A-Za-f]+)', view_url)
        if video_id:
            video_id = video_id.group(1)
            if self.already_downloaded(video_id):
                print('早已下载过{}'.format(view_url))
                return True

            try:
                request = RequestManager(config.headers, config.proxies)
                res = request.get(view_url)

                if res:
                    view_html = res.text
                    title = re.search(r'\<title\>(.+?)\s*-\s*Pornhub\.com\</title\>', view_html)
                    if title:
                        title = title.group(1)
                    else:
                        title = re.search(r'\<title\>(.+?)\</title\>', view_html).group(1)
                    title = html.unescape(title)                               #转换html实体，如&hellip;转换为省略号
                    title = re.sub(r'[\/\\\*\?\|/:"<>\.]', '', title)               #有的html实体也会转化出非法路径字符，也要去掉
                    print('title    : {}'.format(title))

                    dir_path = os.path.join(config.path, title)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)

                    cover_url = re.search(r'\<meta property="og:image".+?content="(http.+?)".+?/\>', view_html).group(1)
                    img = request.get(cover_url)
                    if img:
                        print('cover url: {}'.format(cover_url))
                        with open(dir_path+'/cover.jpg', 'wb')as f:
                            f.write(img.content)
                        
                        #r = re.search(r'media_0;.*?(var.+?)flashvars', view_html)
                        r = re.search(r'\<script type="text/javascript"\>\s*?(var flashvars.+?)\</script\>', view_html, re.S)
                        
                        js_code = r.group(1)
                        if js_code:
                            res = self.get_max_quality_master_file(js_code)
                            if res:
                                quality, quality_url = res[0], res[1]
                                print('get {:>4}P master: {}'.format(quality, quality_url))
                                #print('get media: {}'.format(media_url))

                                root_path_url = re.search(r'(http.+?\.mp4/)', quality_url)
                                if root_path_url:
                                    root_path_url = root_path_url.group(1)

                                    res = self.get_max_quality_index_file(quality_url)
                                    if res:
                                        quality_url = root_path_url + res
                                        print('get {:>4}P index: {}'.format(quality, quality_url))

                                        m3u8_downloader = M3U8Downloader(root_path_url, quality_url, title, title+'.mp4')
                                        result = m3u8_downloader.run()
                                        if result:
                                            success = True

                                #     headers = {
                                #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.74 Safari/537.36 Edg/79.0.309.43',
                                #         'Referer': view_url        
                                #     }

                                #     res = request.get(media_url, headers)
                                #     if res:                            
                                #         max_quality_res = self.get_max_quality(res.text)
                                        # if max_quality_res:
                                        #     quality, quality_url = max_quality_res
                                                # quality_url = root_path_url + quality_url
                                                # print('get {:>4}P: {}'.format(quality, quality_url))

                                # video_m3u8_page = request.get(quality_url)
                                # if video_m3u8_page:
                                #     for line in video_m3u8_page.text.split('\n'):
                                #         relative_path_url = re.search(r'(index-.+?\.m3u8.+?)$', line)
                                #         if relative_path_url:
                                #             video_m3u8_url = root_path_url + relative_path_url.group(1)
                                            
                                            #print(root_path_url, video_m3u8_url)
                                            #print('main m3u8: {}'.format(video_m3u8_url))
                                                    
                if success:
                    mp4_path = os.path.join(config.root_path, title, title+'.mp4')
                    self.download_success(video_id, start_time, mp4_path)
                else:
                    print('视频{} 下载失败'.format(view_url))
                    self.download_failed(video_id)

            except Exception as e:
                print('错误：{}'.format(e))
                print('视频{} 下载失败'.format(view_url))
                self.download_failed(video_id)
        

    def download_some(self, urls_txt):
        with open(urls_txt, 'r')as f:
            urls = f.read()
        urls_list = []
        for url in urls.split('\n'):
            if url[:4] == 'http':
                urls_list.append(url)
        #print(urls_list)
        for i, view_url in enumerate(urls_list):
            print('批量视频下载进度： {:>4}/{:<4}'.format(i+1, len(urls_list)))
            self.download_one(view_url)
            print('\n')


    # 从view_html中的js代码中，拼接出get_media的url
    def get_max_quality_master_file(self, js_code):
        js_code = re.sub(r'var nextVideoPlaylistObject.*$', '', js_code, re.M, re.S)

        #media_name = sorted(list(set(re.findall(r'media_\d+?', js_code))))
        # 大部分形如['media_0', 'media_1', 'media_2', 'media_3', 'media_4', 'media_5']，
        # 也有['media_0', 'media_1', 'media_2', 'media_3', 'media_4'] （https://cn.pornhub.com/view_video.php?viewkey=ph61f8d177a4008）
        # 最后一个是json格式的，视频是整个文件形式的
        # 前面的几个都是m3u8格式的
        # 倒数第二个也是m3u8格式的，是所有格式的m3u8链接
        # 又改版了，上面的注释失效

        #js_obj = execjs.compile(js_code)
        #master_url = js_obj.eval(media_name[-2])

        res = re.search(r'var flashvars_\d+?\s*?=\s*?({.+});\s*?var\splayer_mp4_seek.+$', js_code, re.M)
        if res:
            json_data = json.loads(res.group(1))
            # quality_list = json_data["defaultQuality"]
            # max_quality = max(quality_list)

            max_quality = 0

            for quality_info in json_data["mediaDefinitions"]:
                if type(quality_info["quality"]) != type([]):           # eg. [240, 480, 720]
                    if int(quality_info["quality"]) > max_quality:
                        max_quality = int(quality_info["quality"])
                        max_quality_url = quality_info["videoUrl"]
            
            if max_quality != 0:
                return max_quality, max_quality_url
            
        return None
    

    def get_max_quality_index_file(self, max_quality_url):
        request = RequestManager(config.headers, config.proxies)
        res = request.get(max_quality_url)
        if res:
            res = re.search(r'\n(index.+?)\n', res.text, re.M)
            if res:
                return res.group(1)
        return None
        

    # 选择最高清晰度，最大1080P(2160P等也会出现在列表中，但是需要会员才能解析)
    def get_max_quality(self, master_data):
        res = re.findall(r'#EXT-X-STREAM-INF:.+?RESOLUTION=\d+?x(\d+?),', master_data)
        max_quality = sorted(list(map(int, res)))[-1]
        max_quality_url = re.search(r'#EXT-X-STREAM-INF:.+?RESOLUTION=\d+?x{}.+?(index.+?)\n'.format(max_quality), master_data, re.S).group(1)
        return max_quality, max_quality_url

    
    def already_downloaded(self, video_id):
        if not os.path.exists('SAVED.txt'):
            return False
        with open(r'SAVED.txt')as f:
            ids = f.read()
        return video_id in ids.split('\n')


    def download_success(self, video_id, start_time, mp4_path):
        log_path = r'SAVED.txt'
        with open(log_path, 'a+')as f:
            f.write(video_id+'\n')
        
        fsize = os.path.getsize(mp4_path)
        fsize = round(fsize/float(1024*1024), 2)

        end_time = time.perf_counter()
        print('本视频大小%dMB, 下载时间%d分%.2f秒，平均下载速度为%.2fMB/s' % (fsize, (end_time-start_time)//60, (end_time-start_time)%60, fsize/(end_time-start_time)))


    def download_failed(self, video_id):
        log_path = r'FAILED.txt'
        with open(log_path, 'a+')as f:
            f.write(video_id+'\n')



if __name__ == '__main__':
    #view_url = 'https://cn.pornhub.com/view_video.php?viewkey=phxxxxxxxxxx'
    #pd = PornhubDownloader(view_url = view_url)

    urls_txt = r'pornhub_urls.txt'
    pd = PornhubDownloader(urls_txt = urls_txt)