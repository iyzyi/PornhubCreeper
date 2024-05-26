# PornhubCreeper

Pornhub爬虫🥰

从私有库里拉出来开源啦~

推荐搭配[iyzyi/VideoViewer: Pornhub Xvideos 本地视频浏览](https://github.com/iyzyi/VideoViewer)使用。

## 使用

1. 安装ffmpeg

2. 修改`config.py`中的配置

3. 在`pornhub.py`中，有两种调用方式：

   ```
   # 下载单个视频（指定一个URL）
   view_url = 'https://cn.pornhub.com/view_video.php?viewkey=phxxxxxxxxxx'
   pd = PornhubDownloader(view_url = view_url)
   
   # 下载多个视频（指定一个TXT，其中一行对应一个URL）
   urls_txt = r'pornhub_urls.txt'
   pd = PornhubDownloader(urls_txt = urls_txt)
   ```

4. 下载成功后，会将视频号保存到`SAVED.txt`；下载时发现视频已失效，则将视频号保存到`FAILED.txt`。避免重复下载。
5. 可通过`get_favorite_urls.py`来将收藏夹中所有的Pornhub视频URL提取到`pornhub_urls.txt`中。

