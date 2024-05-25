import re, sys, os

html = r'bookmarks_2024_4_24.html'
filename = 'pornhub_urls.txt'
with open(html,'r',encoding='utf-8') as f1:
    with open(filename,'w',encoding='utf-8') as f2:
        for line in f1:
            url = re.search(r'"(https://.*?pornhub\.com/view_video\.php\?viewkey=.+?)"',line)
            if url:
               f2.write(url.group(1)+'\n')
               #print(url.group(1))
                
with open('pornhub_urls.txt','r',encoding='utf-8') as f2:
    print(len(f2.readlines()))

path = '\\'.join(sys.argv[0].split('\\')[:-1])
print(os.path.join(path, filename))