Pinyin Toolkit
==============

An addon for Mandarin Chinese pinyin in the Anki Spaced Repetition System (http://ankisrs.net/)

Addon page at https://ankiweb.net/shared/info/2554990764<br>
Documentation at http://batterseapower.github.io/pinyin-toolkit/<br> 
Google Discussion Group at http://is.gd/LK9v2g<br>
List of issues at https://github.com/chatch/pinyin-toolkit/issues<br>

<h4>Building the plugin</h4>
```
git clone https://github.com/chatch/pinyin-toolkit.git
git submodule init
git submodule update
cd pinyin-toolkit
python pinyin/db/builder.py
./make_zip.sh                   # build package for upload to anki addons page
cp -rf * ~/Anki/addons          # install direct to local addons directory
```
