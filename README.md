# get_image_from_flickr.py

## about

Serching & downloading image files from [Flickr](https://www.flickr.com/).

It using the `flickr.photos.search` API.

## requirements

```
requests>=2.12.3
```

## usage

Please prepare a text file with API key written.

default: `./key.txt`

```
usage: get_image_from_flickr.py [-h] (-w WORD | -i INPUTFILE) [-o OUTPUT]
                                [-k KEYFILE] [-l LICENSE]
                                [--per_page PER_PAGE]
                                [--start_page START_PAGE]
                                [--max_page MAX_PAGE] [--originalsize]

Search & get images from flickr

optional arguments:
  -h, --help            show this help message and exit
  -w WORD, --word WORD  search query word
  -i INPUTFILE, --inputfile INPUTFILE
                        search query list file
  -o OUTPUT, --output OUTPUT
                        download target dir
  -k KEYFILE, --keyfile KEYFILE
                        api key file
  -l LICENSE, --license LICENSE
                        license level at www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
  --per_page PER_PAGE   number of photos to return per page
  --start_page START_PAGE
                        number of pages to start downloading
  --max_page MAX_PAGE   maximum number of pages to download
  --originalsize        download original image(warning: give a heavy load to
                        network!!)
```
