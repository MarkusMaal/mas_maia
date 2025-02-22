import os, subprocess, time, re, hashlib
from sys import platform
from getpass import getpass
from striprtf.striprtf import rtf_to_text
from flask import Flask, redirect, url_for, request, session, send_file, abort, render_template_string, render_template, json
#from flaskext.mysql import MySQL
import mysql.connector
import datetime
from werkzeug.exceptions import HTTPException

class Version:
    def __init__(self, root):
        # drive letters (for Windows)
        self.letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[::-1]
        self.drives = os.popen("ls -A1 /internal_storage/").read().split("\n")[:-1]
        self.root = root
        self.firsttime = True
        self.home = ""
        # computer info
        masinfo, self.rootfolder = self.LocateData()
        self.CanExit = False
        self.Edition = masinfo[1]
        self.Version = float(masinfo[2])
        self.Build = masinfo[3]
        self.Configured = bool(masinfo[4].replace("Yes", "True").replace("No", "False"))
        self.User = masinfo[5]
        self.Language = masinfo[6]
        self.WinVer = masinfo[7]
        self.Features = masinfo[8].split("-")
        self.PIN = int(masinfo[9])
        self.Name = masinfo[10]
        self.Verifile2 = "BYPASS"
        self.VerifileCheck()
        # linux drive mount prefixes
        self.HD_PREFIX = "/internal_storage/"
        self.FLASH_PREFIX = "/run/media/" + os.getlogin() + "/"
        self.ID = masinfo[11]
        self.HDD = self.LocateHDD()
        if platform == "win32":
            self.Kernel = os.popen("@for /f \"delims=\" %a in ('ver') do @echo %a").read()
        elif platform == "linux" or platform == "linux2":
            self.Kernel = os.popen("uname -sr").read()
        # scheme.cfg
        f = open(self.rootfolder + "/scheme.cfg", "r", encoding="UTF-8")
        self.Color = f.readlines()[0].split(";")
        self.Bg = self.Color[0].split(":")
        self.Fg = self.Color[1].split(":")
        self.HexBg = [hex(int(self.Bg[0])), hex(int(self.Bg[1])), hex(int(self.Bg[2]))]
        self.HexFg = [hex(int(self.Fg[0])), hex(int(self.Fg[1])), hex(int(self.Fg[2]))]
        self.HexBgStr = "#"
        self.HexFgStr = "#"
        self.Wallpaper = []
        self.WallpaperMini = []
        self.WallpaperLogin = []
        self.WallpaperCommon = []
        self.flashdriveroot = self.LocateFlash()
        for i in range(len(self.HexBg)):
            self.HexBg[i] = self.HexBg[i].replace("0x", "")
            if len(self.HexBg[i]) == 1:
                self.HexBg[i] = "0" + self.HexBg[i]
            self.HexBgStr += self.HexBg[i]
        for i in range(len(self.HexFg)):
            self.HexFg[i] = self.HexFg[i].replace("0x", "")
            if len(self.HexFg[i]) == 1:
                self.HexFg[i] = "0" + self.HexFg[i]
            self.HexFgStr += self.HexFg[i]
        # mas.cnf
        self.SHOW_LOGO = False
        self.SCHEDULE_TASKS = False
        self.DESKTOP_NOTES = False
        with open(root + "/mas.cnf", "r", encoding="UTF-8") as masconfig:
            mcnf = masconfig.read().strip().split(";")
            self.SHOW_LOGO = mcnf[0] == "true"
            self.SCHEDULE_TASKS = mcnf[1] == "true"
            self.DESKTOP_NOTES = mcnf[2] == "true"

    def LoadBackgrounds(self):
        with open(self.root + "/bg_desktop.png", "rb") as bg:
            while (byte := bg.read(1)):
                self.Wallpaper.append(byte)
        with open(self.root + "/bg_login.png", "rb") as bg:
            while (byte := bg.read(1)):
                self.WallpaperLogin.append(byte)
        with open(self.root + "/bg_uncommon.png", "rb") as bg:
            while (byte := bg.read(1)):
                self.WallpaperMini.append(byte)
        with open(self.root + "/bg_common.png", "rb") as bg:
            while (byte := bg.read(1)):
                self.WallpaperCommon.append(byte)

    def ReloadDrives(self):
        self.drives = os.popen("ls -A1 /internal_storage/").read().split("\n")[:-1]

    def UserfriendlyVerifile(self):
        if self.Verifile2 == "VERIFIED":
            return "Markuse asjade süsteemi püsivus korras"
        if self.Verifile2 == "TAMPERED":
            return "Kriitilisi faile on modifitseeritud ilma märgistusvahendita"
        if self.Verifile2 == "LEGACY":
            return "Verifile 2.0 pole saadaval"
        if self.Verifile2 == "FOREIGN":
            return "Tegu pole Markuse arvutiga"
        if self.Verifile2 == "FAILED":
            return "Kontrolli sooritamine nurjus"
        if self.Verifile2 == "BYPASS":
            return "Kontroll jäeti vahele"

    def VerifileCheck(self):
        if not os.path.exists(self.root + "/verifile2.jar"):
            self.Verifile2 = "LEGACY"
        if platform == "linux" or platform == "linux2":
            self.Verifile2 = os.popen("java -jar \"" + self.root + "/verifile2.jar\" 2>/dev/null").read().strip()
        elif platform == "win32":
            self.Verifile2 = os.popen("java -jar \"" + self.root + "/verifile2.jar\" 2>nul").read().strip()

    def SaveConfig(self):
        with open(self.root + "/mas.cnf", "w", encoding="UTF-8") as masconfig:
            masconfig.write("true" if self.SHOW_LOGO else "false")
            masconfig.write(";")
            masconfig.write("true" if self.SCHEDULE_TASKS else "false")
            masconfig.write(";")
            masconfig.write("true" if self.DESKTOP_NOTES else "false")
            masconfig.write(";")

    def LocateHDD(self):
        if platform == "win32":
            for dir in self.letters:
                if os.path.exists(dir + ":"):
                    for dir2s in os.listdir(dir + ":"):
                        if os.path.exists(dir + ":/.userdata/users.txt"):
                            return dir + ":"
            return "null"
        elif platform == "linux" or platform == "linux2":
            for dir in self.drives:
                for dir2s in os.listdir(self.HD_PREFIX + dir):
                    if os.path.exists(self.HD_PREFIX + dir + "/.userdata/users.txt"):
                        return self.HD_PREFIX + dir
            return "null"

    def LocateFlash(self):
        if platform == "win32":
            for dir in self.letters:
                if os.path.exists(dir + ":"):
                    for dir2s in os.listdir(dir + ":"):
                        try:
                            for dir3s in os.listdir(dir + ":/" + dir2s):
                                if os.path.exists(dir + ":/" + dir2s + "/edition.txt"):
                                    return dir + ":/"
                        except:
                            pass
        elif platform == "linux" or platform == "linux2":
            for dir in os.popen("ls -A1 " + self.FLASH_PREFIX).read().split("\n")[:-1]:
                for dir2s in os.listdir(self.FLASH_PREFIX + dir):
                    try:
                        for dir3s in os.listdir(self.FLASH_PREFIX + dir + "/" + dir2s):
                            if os.path.exists(self.FLASH_PREFIX + dir + "/" + dir2s + "/edition.txt"):
                                return self.FLASH_PREFIX + dir + "/"
                    except:
                        pass
            return "null"
        return "null"

    def auth(self, authcode, ip):
        whitelist = open(maiaroot + "/whitelist.txt").readlines()
        self.VerifileCheck()
        if not self.Verifile2 == "VERIFIED":
            return False
        if ip == "127.0.0.1" or ip == "localhost":
            return True
        for line in whitelist:
            print(line)
            if line.strip().split(" ")[0] == authcode:
                return True
        return False

    def LocateData(self):
        masinfo = []
        rootfolder = self.root
        fail = open(rootfolder + "/edition.txt", "r", encoding="UTF-8")
        for rida in fail:
            masinfo.append(rida.strip())
        return masinfo, rootfolder

    # events.txt
    def GetScheduledTasks(self):
        out = ""
        with open(self.root + "/events.txt", "r", encoding="UTF-8") as events:
            out = events.read()
        return out

    def SaveScheduledTasks(self, text):
        with open(self.root + "/events.txt", "w", encoding="UTF-8") as events:
            events.write(text)

    
    def GetFriendlySize(self, capacity, ignore_gib=False):
        if capacity < 1000:
            return f"{capacity} B"
        elif capacity < 1000000:
            unit = "k"
            binary_size = capacity / 1024.0
            decimal_size = capacity / 1000.0
        elif capacity < 1000000000:
            unit = "M"
            binary_size = capacity / 1048576
            decimal_size = capacity / 1000000.0
        elif capacity < 1000000000000:
            unit = "G"
            binary_size = capacity / 1073741824.0
            decimal_size = capacity / 1000000000.0
        elif capacity < 1000000000000000:
            unit = "T"
            binary_size = capacity / 1099511627776.0
            decimal_size = capacity / 1000000000000.0
        elif capacity < 1000000000000000000:
            unit = "P"
            binary_size = capacity / 1125899906842624.0
            decimal_size = capacity / 10000001000000000.0
        else:
            unit = "E"
            binary_size = capacity / 1152921504606846976.0
            decimal_size = capacity / 1000000000000000000.0

        if not ignore_gib:
            return f"{round(decimal_size, 2)} {unit}B ({round(binary_size, 2)} {unit}iB)"
        else:
            return f"{round(decimal_size, 2)} {unit}B"




rootpass = "defPassWD345"

root = "C:/mas"
username = os.getlogin()
if platform == "win32":
    root = "C:/mas"
elif platform == "linux" or platform == "linux2":
    root = "/home/" + username + "/.mas"
else:
    print("Not Windows or Linux system!")
    root = None
print(root)
computer = Version(root)
maiaroot = root + "/maia"
# serveri seadistamine
app = Flask(__name__)
serverport = 14414
serverhost = "0.0.0.0"

# juhusliku võtme genereerimine
os.urandom(24)
SECRET_KEY = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'
app.config['SECRET_KEY'] = SECRET_KEY

app.config['FLASK_ENV'] = "development"
# andmebaasi nimi
#mysql = None
#try:
mysql = mysql.connector.connect(user="root", password=rootpass, host="localhost", database="markustegelane")
#except:
#    pass
#mysql.init_app(app)

# Windows-only
def process_exists(process_name):
    if platform == "win32":
        progs = str(subprocess.check_output('tasklist'))
        print("Checking Windows processes...")
        if process_name in progs:
            return True
        else:
            return False

def MakeBreadcrumb(prefix, path):
    out = "<nav style=\"box-shadow: none;\" class=\"white\"><div style=\"overflow: auto; white-space: nowrap;\" class=\"nav-wrapper\">"
    link = prefix
    if prefix == "/":
        link = prefix + "."
    out += "<a href=\"" + prefix + "\" class=\"breadcrumb\">Juur</a>"
    for folder in path.split("/"):
        if folder == "": continue
        out += "<a href=\"" + link + "/" + folder + "\" class=\"breadcrumb\">" + folder + "</a>"
        link += "/" + folder
    out += "</div></nav>"
    return out

def CheckExts(ftype, name, exts, ntype):
    for ext in exts:
        if name.strip().lower().endswith("." + ext) :
            return ntype
    return ftype

def ListDir(prefix, abs_path, dirs, files, fsdir):
    out = "<div class=\"collection\">"
    if prefix == "/":
        prefix = "/."
    if "/" in abs_path[:-1]:
        out += "<a style=\"color: #77b;\" href=\"" + prefix + "/" + "/".join(abs_path.split("/")[:-1]) + "/\" class=\"collection-item\"><i class=\"material-icons circle inline-icon\" style=\"margin-right: 10px;\">folder</i>..</a>"
    else:
        out += "<a style=\"color: #77b;\" href=\"" + prefix + "/\" class=\"collection-item\"><i class=\"material-icons circle inline-icon\" style=\"margin-right: 10px;\">folder</i>..</a>"
    for dir in sorted(dirs, key=str.casefold):
        out += "<a style=\"color: #77b;\" href=\"" + prefix + "/" + os.path.join(abs_path, dir) + "\" class=\"collection-item\"><i class=\"material-icons circle inline-icon\" style=\"margin-right: 10px;\">folder</i>" + dir + "</a>"
    i = 0
    img_exts = ["png", "jpg", "jpeg", "jpe", "jxl", "gif", "webp", "avif", "tif", "tiff", "bmp", "svg", "ico"]
    mov_exts = ["mov", "mp4", "avi", "mpg", "ogv", "mkv", "webm", "flv", "vob", "drc", "mts", "m2ts", "wmv", "asf", "yuv", "3gp", "mxf", "nsv", "m4v"]
    mus_exts = ["aa", "aac", "act", "aiff", "alac", "flac", "amr", "ape", "au", "awb", "dss", "dvf", "gsm", "iklax", "ivs", "m4a", "m4b", "m4p", "mmf", "movpkg", "mp3", "mpc", "msv", "ogg", "oga", "mogg", "opus", "tta", "vox", "wav", "wma", "wv", "cda", "mid", "midi", "sf2", "mod", "xm", "s2m", "s3m", "it", "psm"]
    cod_exts = ["cs", "c", "h", "asm", "bf", "php", "py", "pyc", "js", "java", "html", "xml", "bat", "cmd", "sh", "rs", "cpp", "o", "pdb", "jsp", "json", "htm", "bas", "vb", "r", "m", "rpyc", "lxk", "rcc", "lua", "toml", "action", "abs", "luac", "vbs", "asi", "src", "scb", "mom", "pl", "html5", "mf", "css", "scss", "ss", "rss", "gradle", "mvn", "nt", "ps1", "j", "c++", "as", "lisp", "lol", "qs", "tpl", "ps2", "vbscript", "xbs", "ssq"]
    txt_exts = ["txt", "log", "ini", "inf", "md"]
    exe_exts = ["exe", "scr", "com", "appimage", "app", "dll", "so"]
    arc_exts = ["zip", "7z", "rar", "tar", "gz", "xz", "jar", "apk", "wpk"]
    mas_exts = ["sf", "cfg", "cnf", "unlock", "reg", "bscfg", "bs2cfg", "bs3cfg"]
    ima_exts = ["iso", "img", "ima", "dd", "vhd", "vhdx", "vmdk", "qcow2", "vdi"]
    for file in sorted(files, key=str.casefold):
     ftype = "insert_drive_file"
     ftype = CheckExts(ftype, file, mov_exts, "movie")
     ftype = CheckExts(ftype, file, mus_exts, "music_note")
     ftype = CheckExts(ftype, file, cod_exts, "code")
     ftype = CheckExts(ftype, file, txt_exts, "short_text")
     ftype = CheckExts(ftype, file, exe_exts, "apps")
     ftype = CheckExts(ftype, file, arc_exts, "archive")
     ftype = CheckExts(ftype, file, mas_exts, "settings")
     ftype = CheckExts(ftype, file, ima_exts, "sd_card")
     ftype = CheckExts(ftype, file, img_exts, "image")
     try:
        out += "<a id=\"file" + str(i) + "\" href=\"#/\" onclick=\"getFile('file"+str(i)+"')\" data-target=\"modal1\" style=\"color: #77b;\" class=\"collection-item modal-trigger\"><i class=\"material-icons circle inline-icon\" style=\"margin-right: 10px;\">" + ftype + "</i>" + file + "<span style='opacity: 0; position: absolute; right: 1em; font-size: 0.9em'>" + computer.GetFriendlySize(os.path.getsize(os.path.join(fsdir, abs_path, file)), True) + "</span>" + "</a>"
     except:
        out += "<a id=\"file" + str(i) + "\" href=\"#/\" onclick=\"getFile('file"+str(i)+"')\" data-target=\"modal1\" style=\"color: #77b;\" class=\"collection-item modal-trigger\"><i class=\"material-icons circle inline-icon\" style=\"margin-right: 10px;\">" + ftype + "</i>" + file + "<span style='opacity: 0; position: absolute; right: 1em; font-size: 0.9em'>" + computer.GetFriendlySize(-1, True) + "</span>" + "</a>"
     i = i + 1
    out += "</div>"
    return out


def CollectFsEntries(path):
    dirs = [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
    files = [x for x in os.listdir(path) if not os.path.isdir(os.path.join(path, x))]
    return dirs, files


def openfile(path):
    return open(path, "r", encoding="UTF-8").read().replace("computer.flashdriveroot", computer.LocateFlash()).replace(
        "computer.hdd", computer.LocateHDD())


def render_page(uri):
    page = render_template_string(openfile((maiaroot + "/html_root/head.html")) + \
                                  openfile((maiaroot + uri)) + \
                                  openfile((maiaroot + "/html_root/foot.html")), SESSION=session, os=os, computer=computer, subprocess=subprocess)
    return page


def render_page_string(string, path="", wallpapers=None, elements=None):
    if wallpapers is None:
        wallpapers = []
    page = render_template_string(openfile((maiaroot + "/html_root/head.html")) +
                                  string +
                                  openfile((maiaroot + "/html_root/foot.html")), SESSION=session, PATH=path, os=os,
                                  wallpapers=wallpapers, elements=elements, computer=computer,
                                  fswallpapers=os.listdir(maiaroot + "/images"))
    return page


@app.route("/add_dev", methods=["POST", "GET"])
def add_dev():
    if platform == "windows":
        if process_exists("Markuse arvuti lukustamis"):
            return render_page_string("Arvuti on hetkel lukustatud. Seadme lisamise funktsioon pole sellises olukorras saadaval.")
    if session:
        if request.method == "POST":
            ip_str = request.form["ip"]
            type_str = request.form["type"]
            whitelist = open(maiaroot + "/whitelist.txt", "a", encoding="UTF-8")
            whitelist.write(ip_str + " - " + type_str + "\n")
            whitelist.close()
            return redirect("/")
        else:
            return render_page("/html_root/add_dev.html")
    else:
        return redirect("/")


@app.route("/remove_dev", methods=["GET"])
def rem_dev():
    if session:
        str = request.args["str"].split("-")
        full_str = str[0] + "." + str[1] + "." + str[2] + "." + str[3] + " - " + str[4]
        whitelist = open(maiaroot + "/whitelist.txt", "r", encoding="UTF-8")
        all_lines = whitelist.readlines()
        whitelist.close()
        new_file = open(maiaroot + "/whitelist.txt", "w", encoding="UTF-8")
        for line in all_lines:
            if not line.strip() == full_str:
                new_file.write(line)
        new_file.close()
        return redirect("/")
    else:
        return redirect("/")


@app.route("/mas_db/faq", methods=["GET"])
def mas_faq():
    return render_page("/mas_db/faq.html")

@app.route("/swap_versions", methods=["GET"])
def SwapMiniFull():
    if session and computer.auth(session["code"], safeip(request)):
        print("Deleting left/right desktop backgrounds")
        os.popen("rm \"" + root + "/bg_desktop_l.png\"")
        os.popen("rm \"" + root + "/bg_desktop_r.png\"")
        print("Swapping desktop backgrounds")
        os.popen("mv \"" + root + "/bg_desktop.png\" \"" + root + "/temp.png\" && mv \"" + root + "/bg_uncommon.png\" \"" + root + "/bg_desktop.png\" && mv \"" + root + "/temp.png\" \"" + root + "/bg_uncommon.png\"")
        print("Creating left/right desktop backgrounds")
        os.popen("magick \"" + root + "/bg_desktop.png\" -crop 1280x1024+0+56 \"" + root + "/bg_desktop_l.png\" && magick \"" + root + "/bg_desktop.png\" -crop 1280x1024+3200+56 \"" + root + "/bg_desktop_r.png\" && sh " + root + "/change_bg.sh")
        return redirect("/")
    else:
        return redirect("/")

@app.route("/runcmd", methods=["POST"])
def runcmd():
    if request.method == "POST" and session:
        if computer.auth(session["code"], safeip(request)):
            if request.form["command"][:2] == "rm" or request.form["command"][:2] == "dd":
                session["comamnd"] = "echo \"This command is blacklisted.\""
                return redirect("/")
            session["command"] = request.form["command"]
        return redirect("/")
    else:
        return redirect("/")

@app.route("/crd_toggle", methods=["GET"])
def toggle_crd():
    if 'running' in subprocess.check_output('[ "$(ps -ef | grep krfb | wc -l)" -gt "3" ] && echo "running" || echo "idle"', shell=True, text=True):
        os.system("pkill -9 krfb")
        time.sleep(1)
        return redirect("/")
    else:
        os.system("WAYLAND_DISPLAY=wayland-0 krfb --nodialog & disown")
        time.sleep(2)
        return redirect("/")

@app.route("/mas_db/upload_wallpaper", methods=["GET", "POST"])
def add_wallpaper():
    if not session:
        return redirect("/")
    else:
        if request.method == "POST":
            if computer.auth(session["code"], safeip(request)):
                f = request.files['file']
                f.save(maiaroot + "/images/" + f.filename)
                return render_page_string("<p>Fail laaditi üles</p><a class=\"btn deep-purple lighten-2 waves-effect waves-light\" href=\"/\">Tagasi avalehele</a>")
            else:
                return redirect("/")
        else:
            return redirect("/mas_db/wallpapers")


@app.route("/mas_db/chain_wallpaper", methods=["GET", "POST"])
def chain_wallpaper():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            cursor = mysql.cursor()
            cursor.execute("INSERT INTO mas_wallpapers (ASUKOHT, VERSIOONI_ID) VALUES (\"" + request.form["location"] + \
                           "\", " + request.form["ver_id"] + ")")
            mysql.commit()
            mysql.close()
            return redirect("/mas_db/wallpapers")
        else:
            return redirect("/")


@app.route("/mas_db/remove_wallpaper", methods=["GET", "POST"])
def remove_wallpaper():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            cursor = mysql.cursor()
            cursor.execute("DELETE FROM mas_wallpapers WHERE ID = " + request.form["id"])
            mysql.commit()
            mysql.close()
            return redirect("/mas_db/wallpapers")
        else:
            return redirect("/")


@app.route("/mas_db/add", methods=["GET", "POST"])
def add_record():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            if request.method == "POST":
                cursor = mysql.cursor()
                cmd = "INSERT INTO mas_db (VERSIOON, LVERSIOON, AASTA, NIMI, KIRJELDUS, MINI) VALUES ("
                cmd += request.form["fver"] + ", "
                cmd += request.form["lver"] + ", "
                cmd += request.form["year"] + ", \""
                cmd += request.form["title"] + "\", \""
                cmd += request.form["description"] + "\", "
                if "boolmini" in request.form:
                    cmd += "1)"
                else:
                    cmd += "0)"
                cursor.execute(cmd)
                mysql.commit()
                mysql.close()
                return redirect("/mas_db")
            else:
                return render_page("/html_root/new_version.html")
        else:
            return redirect("/")

@app.route("/mas_db/update", methods=["GET", "PUT"])
def update_record():
    if not session:
        return redirect("/")
    else:
        return render_page_string("<p>Konstrueerimisel</p>")

@app.route("/mas_db/remove", methods=["GET", "DELETE"])
def remove_record():
    if not session:
        return redirect("/")
    else:
        return render_page_string("<p>Konstrueerimisel</p>")

@app.route("/mas_db/wallpapers")
def wallpapers():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM mas_wallpapers")
            wallpapers = cursor.fetchall()
            idpo = len(wallpapers) + 1
            cursor.execute("SELECT * FROM mas_db")
            elements = cursor.fetchall()
            return render_page_string(openfile(maiaroot + "/html_root/upload_picture.html"), str(idpo), wallpapers,
                                      elements=elements)
        else:
            return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return render_page_string("<p>Sessioon katkestatud</p>")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            if request.method == 'POST':
                f = request.files['file']
                p = request.args["path"]
                p = p[0] + ":" + p[1:]
                f.save(p + "/" + f.filename)
                return render_page_string("<p>Fail laaditi üles</p><a class=\"btn green lighten-2 waves-effect waves-light\"href=\"/\">Tagasi avalehele</a>")
            else:
                return redirect("/")
        else:
            return redirect("/")


@app.route("/get", methods=["GET"])
def getIP():
    return render_page_string(safeip(request))


@app.route("/mas_db", methods=["GET"])
def mas_db():
    if not request.args:
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM mas_db")
        versioonid = cursor.fetchall()
        out = ""
        if "code" in session and computer.auth(session["code"], safeip(request)):
            out += "<h1>Haldamine</h1>"
            out += "<br><a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db/add\">Lisa kirje</a>&nbsp;&nbsp;" \
                   "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db/update\">Muuda kirjet</a>&nbsp;&nbsp;" \
                   "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db/remove\">Eemalda kirje</a>&nbsp;&nbsp;" \
                   "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db/wallpapers\">Taustapildid</a>&nbsp;&nbsp;"
        out += "<h1>Sisukord</h1>" \
               "<p><a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?all=1\">Kuva kõik versioonid</a></p>" \
               "<p><a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db/faq\">Korduma kippuvad küsimused</a></p>" \
               "<ul class=\"collection\">"
        for versioon in versioonid:
            out += "<a style=\"color: #77b;\" class=\"collection-item\" href=\"/mas_db?id=" + str(versioon[0]) + "\">" + str(versioon[1]) +  " " + str(versioon[4]) + "<span style=\"color: #77b;\" class=\"secondary-content\">" + str(versioon[3]) + "</span></a>"
        out += "</ul>"
        return render_page_string(out)
    else:
        if "id" in request.args:
            cursor = mysql.cursor()
            cursor.execute("SELECT ID FROM mas_db;")
            total = cursor.fetchall()[-1][0]
            id = int(request.args["id"])
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM mas_wallpapers WHERE VERSIOONI_ID = " + str(id))
            wallpapers = cursor.fetchall()
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM mas_db WHERE ID = " + str(request.args["id"]))
            premeta = cursor.fetchall()
            if len(premeta) == 0:
                if not "next" in request.args:
                    return redirect("/mas_db?id=" + str(id - 1))
                else:
                    return redirect("/mas_db?id=" + str(id + 1) + "&next=1")
            meta = premeta[0]
            out = ""
            for wallpaper in wallpapers:
                out += "<a href=\"/images/" + wallpaper[1] + "\"><img style=\"width: 100%\" src=\"/images/" + wallpaper[1] + "\"></a>"
            out += "<h1>" + meta[4] + "</h1>"
            if meta[6]:
                out += "<p>(Miniversioon)</p>"
            if not meta[1] == meta[2]:
                out += "<p>Versioon " + str(meta[1]) + " - " + str(meta[2]) + "</p>"
            else:
                out += "<p>Versioon " + str(meta[1]) + "</p>"
            out += "<p>" + meta[5] + "</p>"
            out += "<p>&copy; " + str(meta[3]) + " Markuse asjad</p>"
            if meta[0] > 1:
                out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?id=1\">&lt;&lt; Esimene</a>&nbsp;&nbsp;"
                out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?id=" + str(meta[0] - 1) + "\">&lt; Eelmine</a>&nbsp;&nbsp;"
            if meta[0] < total:
                out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?id=" + str(meta[0] + 1) + "&next=1\">Järgmine &gt;</a>&nbsp;&nbsp;"
                out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?id=" + str(total) + "\">Viimane &gt;&gt;</a>"
            out += "<hr><div style=\"text-align:center\">"
            out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db?all=1\">Kõik versioonid</a>&nbsp;&nbsp;<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db\">Sisukord</a>"
            out += "</div>"
            return render_page_string(out)
        elif "year" in request.args:
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM mas_db WHERE AASTA = " + str(request.args["year"]))
            versioonid = cursor.fetchall()
            out = "<h1>Aasta " + str(request.args["year"]) + "</h1>"
            for meta in versioonid:
                cursor = mysql.cursor()
                cursor.execute("SELECT * FROM mas_wallpapers WHERE VERSIOONI_ID = " + str(meta[0]))
                wallpapers = cursor.fetchall()
                out += "<hr>"
                for wallpaper in wallpapers:
                    out += "<a href=\"/images/" + wallpaper[1] + "\"><img style=\"max-width: 100%;\" src=\"/images/" + wallpaper[1] + "\"/></a>"
                out += "<a href=\"/mas_db?id=" + str(meta[0]) + "\"><h2>" + meta[4] + "</h2></a>"
                if meta[6]:
                    out += "<p>(Miniversioon)</p>"
                if not meta[1] == meta[2]:
                    out += "<p>Versioon " + str(meta[1]) + " - " + str(meta[2]) + "</p>"
                else:
                    out += "<p>Versioon " + str(meta[1]) + "</p>"
                out += "<p>" + meta[5] + "</p>"
                out += "<p>&copy; " + str(meta[3]) + " Markuse asjad</p>"
            out += "<hr><div style=\"text-align:center\">"
            out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db\">Sisukord</a>&nbsp;&nbsp;<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"#\">Tagasi algusesse</a>"
            out += "</div>"
            return render_page_string(out)
        else:
            cursor = mysql.cursor()
            cursor.execute("SELECT * FROM mas_db")
            versioonid = cursor.fetchall()
            out = "<h1>Kõik versioonid</h1>"
            for meta in versioonid:
                cursor = mysql.cursor()
                cursor.execute("SELECT * FROM mas_wallpapers WHERE VERSIOONI_ID = " + str(meta[0]))
                wallpapers = cursor.fetchall()
                out += "<hr>"
                for wallpaper in wallpapers:
                    out += "<a href=\"/images/" + wallpaper[1] + "\"><img style=\"max-width: 100%;\" src=\"/images/" + wallpaper[1] + "\"></a>"
                out += "<a href=\"/mas_db?id=" + str(meta[0]) + "\"><h2>" + meta[4] + "</h2></a>"
                if meta[6]:
                    out += "<p>(Miniversioon)</p>"
                if not meta[1] == meta[2]:
                    out += "<p>Versioon " + str(meta[1]) + " - " + str(meta[2]) + "</p>"
                else:
                    out += "<p>Versioon " + str(meta[1]) + "</p>"
                out += "<p>" + meta[5] + "</p>"
                out += "<p>&copy; " + str(meta[3]) + " Markuse asjad</p>"
            out += "<hr><div style=\"text-align:center\">"
            out += "<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"/mas_db\">Sisukord</a>&nbsp;&nbsp;<a class=\"waves-effect waves-light btn deep-purple lighten-2\" href=\"#\">Tagasi algusesse</a>"
            out += "</div>"
            return render_page_string(out)

def safeip(request):
    if "HTTP_CF_CONNECTING_IP" in request.environ:
        return request.environ["HTTP_CF_CONNECTING_IP"]
    else:
        return request.remote_addr

@app.route("/", methods=["GET"])
def index():
    computer.VerifileCheck()
    computer.ReloadDrives()
    if not computer.Verifile2 == "VERIFIED":
        redirect("/logout")
    if not session or len(session) < 2:
        ignore = 0
        addr = safeip(request)
        if os.path.exists(computer.rootfolder + "/flash_unlock_is_enabled.log"):
            session["flashunlock"] = True
        if safeip(request) == "127.0.0.1" or safeip(request) == "localhost":
            session["code"] = addr
            session["device"] = "mas"
            time.sleep(0.2)
            if platform == "win32":
                return render_page("/html_root/private.html")
            elif platform == "linux" or platform == "linux2":
                return render_page("/html_root/private_linux.html")
        whitelist = open(maiaroot + "/whitelist.txt").readlines()
        for line in whitelist:
            if line.strip().split(" ")[0] == addr:
                session["code"] = addr
                session["device"] = line.strip().split(" ")[2]
                time.sleep(0.2)
                if platform == "win32":
                    if process_exists("Markuse arvuti lukustamis"):
                        with open(computer.root + "/" + str(datetime.datetime.now().hour) + "." + str(datetime.datetime.now().minute) + ".unlock", "w") as f:
                            f.write("A");
                        time.sleep(2)
                        if os.path.isfile(computer.root + "/" + str(datetime.datetime.now().hour) + "." + str(datetime.datetime.now().minute) + ".unlock"):
                            os.remove(computer.root + "/" + str(datetime.datetime.now().hour) + "." + str(datetime.datetime.now().minute) + ".unlock")
                    return render_page("/html_root/private.html")
                elif platform == "linux" or platform == "linux2":
                    return render_page("/html_root/private_linux.html")
        return redirect("/ip")
    else:
        whitelist = open(maiaroot + "/whitelist.txt").readlines()
        for line in whitelist:
            if line.strip().split(" ")[0] == safeip(request):
                if platform == "win32":
                    return render_page("/html_root/private.html")
                elif platform == "linux" or platform == "linux2":
                    return render_page("/html_root/private_linux.html")
        if safeip(request) == "localhost" or safeip(request) == "127.0.0.1":
            if platform == "win32":
                return render_page("/html_root/private.html")
            elif platform == "linux" or platform == "linux2":
                return render_page("/html_root/private_linux.html")
        return redirect("/ip")


@app.route("/askpin", methods=["GET"])
def askpin():
    if session:
        return render_page_string(openfile(maiaroot + "/html_root/askpin.html"))
    else:
        return redirect("/")


@app.route("/verify_dev", methods=["POST"])
def verify_device():
    print("verify_device")
    if request.method == "POST" and session:
        if platform == "windows":
            if process_exists("Markuse arvuti lukustamis"):
                return render_page_string("Arvuti on hetkel lukustatud. Seadme lisamise funktsioon pole sellises olukorras saadaval.")
        verify_code = str(request.form.get("verifycode")).upper()
        sess_ip = session["code"]
        sess_dev = session["device"]
        reference = ""
        attempts = 0
        while not os.path.exists(maiaroot + "/" + sess_dev + "." + sess_ip.replace(".", "_") + ".maia"):
            attempts += 1
            if attempts > 500:
                break
        if not os.path.exists(maiaroot + "/" + sess_dev + "." + sess_ip.replace(".", "_") + ".maia"):
            return redirect("/")
        with open(maiaroot + "/" + sess_dev + "." + sess_ip.replace(".", "_") + ".maia", "r") as refile:
            reference = refile.read().strip()
        with open(maiaroot + "/" + "close_popup.maia", "w") as outfile:
            outfile.write("1234")
        nonhashed_offline = sess_dev + "__" + verify_code
        hashed_string = hashlib.sha256(nonhashed_offline.encode('utf-8')).hexdigest()
        if hashed_string.upper() == reference:
            with open(maiaroot + "/whitelist.txt", "a") as whitelistout:
                whitelistout.write(sess_ip + " - " + sess_dev + "\n")
        session.clear()
        return redirect("/")


@app.route("/ip", methods=["GET"])
def ip():
    print("ip")
    if process_exists("Markuse arvuti lukustamis"):
        return render_page_string("Arvuti on hetkel lukustatud. Seadme lisamise funktsioon pole sellises olukorras saadaval.")
    whitelist = open(maiaroot + "/whitelist.txt").readlines()
    if not "code" in session:
        ignore = 0
        addr = safeip(request)
        if safeip(request) == "127.0.0.1" or safeip(request) == "localhost":
            session["code"] = addr
            session["device"] = "mas"
            return redirect("/")
        for line in whitelist:
            if line.strip().split(" ")[0] == addr:
                session["code"] = addr
                session["device"] = line.strip().split(" ")[2]
                return redirect("/")
        if len(request.args) > 0:
            if request.args.get("dt") == "unknown":
                return render_page_string(openfile(maiaroot + "/html_root/auth_error.html") + "<p>Selle seadme IP aadress: " + addr + "</p>")
            else:
                with open(maiaroot + "/request_permission.maia", "w", encoding="UTF-8") as outfile:
                    outfile.write(request.args.get("dt") + ";" + request.args.get("ip"))
                    session["code"] = addr
                    session["device"] = request.args.get("dt")
                return redirect("/askpin")
        return render_page_string("<p style=\"margin-top: 50px;\">Palun oota...</p>" + \
                                  "<script>const ip = \"" + addr + "\"; let devtype = \"\";</script><script "
                                                                 "src=\"/js/pre-load.js\" type=\"text/javascript\"/>")
    else:
        if safeip(request) == "127.0.0.1" or safeip(request) == "localhost":
            return redirect("/")
        for line in whitelist:
            if line.strip().split(" ")[0] == session["code"]:
                session["code"] = session["code"]
                session["device"] = line.strip().split(" ")[2]
                return redirect("/")
        session.clear()
        return redirect("/ip")


@app.route("/lock", methods=["GET"])
def lock():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            if platform == "win32":
                os.system("\"" + computer.root + "/Markuse asjad/Markuse arvuti lukustamissüsteem.exe\"")
            elif platform == "linux" or platform == "linux2":
                #os.system("light-locker-command --lock")
                os.system("loginctl lock-session &")
                time.sleep(2)
            return redirect("/")
        else:
            return redirect("/")


@app.route("/unlock", methods=["GET"])
def unlock():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            #os.system("killall light-locker && sleep 5 && $(light-locker)")
            os.system("loginctl unlock-session &")
            time.sleep(1)
            return redirect("/")
        else:
            return redirect("/")

@app.route("/edfu", methods=["GET"])
def edfu():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            if os.path.exists(computer.rootfolder + "/flash_unlock_is_enabled.log"):
                os.system("rm ~/.mas/flash_unlock_is_enabled.log &")
            else:
                os.system("python ~/scripts/device.py &")
            time.sleep(1)
            return redirect("/")
        else:
            return redirect("/")

@app.route("/shutdown", methods=["GET"])
def shutdown():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            device = "Tundmatu seade"
            if session["device"] == "mas":
                device = "Markuse arvuti"
            elif session["device"] == "masv":
                device = "Markuse virtuaalarvuti"
            elif session["device"] == "mta":
                device = "Markuse tahvelarvuti"
            elif session["device"] == "masl":
                device = "Markuse arvuti (Linux)"
            elif session["device"] == "mtel":
                device = "Markuse telefon"
            elif session["device"] == "mat":
                device = "Muu Markuse seade"
            if platform == "win32":
                os.system("shutdown /s /c \"Saadeti väljalülitamise käsklus seadmest " + device + "\"")
            elif platform == "linux" or platform == "linux2":
                os.system("qdbus org.kde.Shutdown /Shutdown logoutAndShutdown")
            return redirect("/logout")
        else:
            return redirect("/")


@app.route("/restart", methods=["GET"])
def restart():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            device = "Tundmatu seade"
            if session["device"] == "mas":
                device = "Markuse arvuti"
            elif session["device"] == "masv":
                device = "Markuse virtuaalarvuti"
            elif session["device"] == "mta":
                device = "Markuse tahvelarvuti"
            elif session["device"] == "masl":
                device = "Markuse arvuti (Linux)"
            elif session["device"] == "mtel":
                device = "Markuse telefon"
            elif session["device"] == "mat":
                device = "Muu Markuse seade"
            if platform == "win32":
                os.system("shutdown /r /c \"Saadeti taaskäivitamise käsklus seadmest " + device + "\"")
            elif platform == "linux" or platform == "linux2":
                os.system("qdbus org.kde.Shutdown /Shutdown logoutAndReboot")
            return redirect("/logout")
        else:
            return redirect("/")

@app.route("/sleep")
def sleep():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)):
            if platform == "win32":
                os.system("%windir%\\System32\\rundll32.exe powrprof.dll,SetSuspendState Standby")
            elif platform == "linux" or platform == "linux2":
                os.system("sudo /root/suspend.sh")
            return redirect("/logout")
        else:
            return redirect("/")

@app.route("/screen")
def make_snip():
    os.system("spectacle -f -b -o ~/.mas/maia/screenshot.png")
    time.sleep(2)
    return render_page("/html_root/screenshot.html")

@app.route("/mas_info")
def mas_info():
    computer = None
    computer = Version(root)
    computer.LocateData()
    computer.LocateHDD()
    computer.LocateFlash()
    out = "<h2>Markuse arvuti asjade teave</h2><table>"
    out += "<tr><td>Nimi</td><td>" + computer.Name + "</td></tr>"
    out += "<tr><td>Versioon</td><td>" + str(computer.Version) + "</td></tr>"
    out += "<tr><td>Väljaanne</td><td>"
    if computer.Edition == "Ultimate":
        out += "<span style=\"color: blueviolet;\">Ultimate</span>"
    elif computer.Edition == "Pro":
        out += "<span style=\"color: deepskyblue;\">Pro</span>"
    elif computer.Edition == "Premium":
        out += "<span style=\"color: darkred;\">Premium</span>"
    elif computer.Edition == "Basic+":
        out += "<span style=\"color: goldenrod;\">Basic+</span>"
    else:
        out += "<span style=\"color: dimgray;\">Tundmatud</span>"
    out += "</td></tr>"
    out += "<tr><td>Järk</td><td>" + computer.Build + "</td></tr>"
    out += "<tr><td>Juurutatud</td><td>" + str(computer.Configured).replace("True", "Jah").replace("False", "Ei") + \
           "</td></tr>"
    out += "<tr><td>Keel</td><td>" + computer.Language + "</td></tr>"
    out += "<tr><td>Kasutaja</td><td>" + computer.User + "</td></tr>"
    out += "<tr><td>Windowsi versioon</td><td>" + computer.WinVer + "</td></tr>"
    out += "<tr><td>Linuxi versioon</td><td>" + computer.Kernel + "</td></tr>"
    out += "<tr><td>Funktsioonid</td><td><ul>"
    for feature in computer.Features:
        if feature == "IP":
            out += "<li>Integratsioonitarkvara</li>"
        elif feature == "IT":
            out += "<li>Interaktiivne töölaud</li>"
        elif feature == "WX":
            out += "<li>Windows 10</li>"
        elif feature == "GP":
            out += "<li>Grupipoliitika</li>"
        elif feature == "LT":
            out += "<li>Livetuner optimeerimised</li>"
        elif feature == "RM":
            out += "<li>Rainmeter</li>"
        elif feature == "DX":
            out += "<li>DesktopX</li>"
        elif feature == "RD":
            out += "<li>Kaugjuhtimine</li>"
        elif feature == "CS":
            out += "<li>Klassikaline stardimenüü</li>"
        elif feature == "TS":
            out += "<li>Standardfunktsioonid</li>"
        elif feature == "MM":
            out += "<li>Markuse asjade tugi</li>"
    out += "</ul></td></tr>"
    out += "<tr><td>Ebaturvaline kontrollnumber</td><td>" + str(computer.PIN) + "</td></tr>"
    out += "<tr><td>Krüptitud kontrollnumber</td><td>" + str(computer.ID) + "</td></tr>"
    out += "<tr><td>M.A.S. backendi juurkaust</td><td>" + computer.rootfolder + "</td></tr>"
    out += "<tr><td>Mälupulga juurkaust</td><td>"
    if computer.flashdriveroot == "null":
        out += "Pole ühendatud või haakumata</td></tr>"
    else:
        out += computer.flashdriveroot + "</td></tr>"
    out += "<tr><td>Kõvaketta asukoht</td><td>"
    if computer.HDD == "null":
        out += "Pole ühendatud või haakumata</td></tr>"
    else:
        out += computer.HDD + "</td></tr>"
    out += "<tr><td>Keskkonna muutujad</td><td>"
    for key in request.environ.keys():
        if not "COOKIE" in key and not "JWT" in key:
            out += key+"="+str(request.environ[key])+"<br>"
    out += "</td></tr>"
    out += "<tr><td>Verifile 2.0 olek</td><td>"
    out += str(computer.Verifile2) + ": " + str(computer.UserfriendlyVerifile())
    out += "</td></tr>"
    out += "</table>"
    return render_page_string(out)


@app.route("/wallpaper")
def wallpaper():
    return open(root + "/desktop/wallpaper.html", "r", encoding="UTF-8").read()


@app.route("/style")
def stylesheet():
    return open(maiaroot + "/style.css", "r", encoding="UTF-8").read()


@app.route("/remote")
def remote():
    return render_page("/html_root/remote.html")


@app.route("/screenshot.png")
def scrnshot():
    if session:
        return send_file(maiaroot + "/screenshot.png")
    else:
        return render_page_string("Juurdepääs keelatud.")

@app.route("/bg", methods=["GET"])
def sendBackground():
    tp = request.args.get("type")
    if tp == "desktop":
        return send_file(root + "/bg_desktop.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "login":
        return send_file(root + "/bg_login.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "common":
        return send_file(root + "/bg_common.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "mobile":
        return send_file(root + "/bg_mobile.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "mobile_lock":
        return send_file(root + "/bg_mobile_lock.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "tablet":
        return send_file(root + "/bg_tablet.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "tablet_lock":
        return send_file(root + "/bg_tablet_lock.png", as_attachment=request.args.get("dload")=="1")
    elif tp == "uncommon":
        return send_file(root + "/bg_uncommon.png", as_attachment=request.args.get("dload")=="1")
    else:
        return render_page_string("Ei leia.")

@app.route("/flash/", methods=["GET"])
@app.route("/flash", methods=["GET"])
def flash():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)) and not computer.flashdriveroot == "null":
            files = None
            try:
                files = os.scandir(computer.flashdriveroot)
            except:
                try:
                    computer.LocateFlash()
                    files = os.scandir(computer.flashdriveroot)
                except:
                    return redirect("/")
            out = "<h2>Markuse mälupulk</h2>"
            edition = open(computer.flashdriveroot + "E_INFO/edition.txt", "r", encoding="UTF-8").read()
            out += "<p>Väljaanne: " + edition + "</p>"
            out += "<h2>Uudised</h2>"
            for i in range(5):
                out += open(maiaroot + "/html_root/newscript.js", "r", encoding="UTF-8").read()
                regex = re.compile('(?:\r\n|\r(?!\n)|\n){2,}')
                try:
                    with open(computer.flashdriveroot + "/E_INFO/uudis" + str(i + 1) + ".rtf") as infile:
                        content = rtf_to_text(rtf_to_text(infile.read()))
                        out += "<div style=\"display: none; padding: 5%; border: 2px solid;\" id=\"uudis" + str(i + 1) + "\">" + "<hr>".join(content.split("\n")) + "</div>"
                except:
                    out += "<div style=\"display: none; color: red; padding: 5%; border 2px solid;\" id=\"uudis" + str(i + 1) + "\">Uudise laadimine nurjus</div>"
                    pass
            out += "<br/><a class=\"waves-effect waves-light btn-large deep-purple lighten-2\" href=\"#/\" onclick=\"prevpage();\">Eelmine uudis</a>"
            out += "<a class=\"waves-effect waves-light btn-large deep-purple lighten-2 secondary-content\" href=\"#/\" onclick=\"nextpage();\">Järgmine uudis</a>"
            if os.path.exists(computer.flashdriveroot + "/Markuse_videod"):
                out += "<h2>Uusimad videod</h2><div class=\"collection icon-blue\">"
                i = 1
                while i < 3:
                    for file in os.listdir(computer.flashdriveroot + "/Markuse_videod"):
                        if file[0] == str(i):
                            out += "<a style=\"color: #77b;\" class=\"icon-blue collection-item\" href=\"/flash/Markuse_videod/" + file + "\">" + file + "</a>"
                            i += 1
                out += "</div>"
                
            dirs, files = CollectFsEntries(computer.flashdriveroot)
            out += "<h2>Failid Markuse mälupulgal</h2>"
            out += ListDir("/flash", "", dirs, files, computer.flashdriveroot)
            out += open(maiaroot + "/html_root/upload.html", "r", encoding="UTF-8").read()
            out += open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8").read()
            return render_page_string(out, path=computer.flashdriveroot)
        else:
            computer.LocateFlash()
            if not computer.flashdriveroot == "null":
                flash()
            return redirect("/")


@app.route("/flash/<path:req_path>/", methods=["GET"])
@app.route("/flash/<path:req_path>", methods=["GET"])
def flashfile(req_path):
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)) and not computer.flashdriveroot == "null":
            abs_path = os.path.join(computer.flashdriveroot, req_path)
            if not os.path.exists(abs_path):
                return abort(404)
            if os.path.isfile(abs_path):
                return send_file(abs_path, as_attachment=("preview" not in request.args))            
            dirs, files = CollectFsEntries(abs_path)
            out = "<h2>Markuse mälupulk</h2>"
            out += MakeBreadcrumb("/flash", abs_path.replace(computer.flashdriveroot, ""))
            out += ListDir("/flash", abs_path.replace(computer.flashdriveroot, ""), dirs, files, computer.flashdriveroot)
            with open(maiaroot + "/html_root/upload.html", "r", encoding="UTF-8") as upload:
                out += upload.read()
            with open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8") as fbrowser:
                out += fbrowser.read()
            return render_page_string(out, path=computer.flashdriveroot + "/" + req_path)
        else:
            return redirect("/")


@app.route("/chg_color", methods=["POST"])
def chgcolor():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)) and not computer.HDD == "null":
            bg_col = request.form.get("bg")
            fg_col = request.form.get("fg")
            bg_array = list(str(int(bg_col[i:i+2], 16)) for i in (1, 3, 5))
            fg_array = list(str(int(fg_col[i:i+2], 16)) for i in (1, 3, 5))
            computer.Bg = bg_array
            computer.Fg = fg_array
            computer.HexBgStr = bg_col
            computer.HexFgStr = fg_col
            with open(root + "/scheme.cfg", "w", encoding="UTF-8") as colorfile:
                colorfile.write(":".join(bg_array) + ":;" + ":".join(fg_array) + ":;")
            computer.SHOW_LOGO = True if not request.form.get("show_logo") == None else False
            computer.SCHEDULE_TASKS = True if not request.form.get("scheduled_tasks") == None else False
            computer.DESKTOP_NOTES = True if not request.form.get("desktop_notes") == None else False
            computer.SaveConfig()
            return redirect("/")
        else:
            return redirect("/")

@app.route("/hdd/", methods=["GET"])
def hdd():
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)) and not computer.HDD == "null":
            dirs, files = CollectFsEntries(computer.HDD)
            out = "<h2>Markuse kaustad</h2>"
            out += ListDir("/hdd", "", dirs, files, computer.HDD)
            out += open(maiaroot + "/html_root/upload.html", "r", encoding="UTF-8").read()
            out += open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8").read()
            return render_page_string(out, path=computer.HDD)
        else:
            return redirect("/")


@app.route("/hdd/<path:re_path>", methods=["GET"])
def hddfile(re_path):
    if not session:
        return redirect("/")
    else:
        if computer.auth(session["code"], safeip(request)) and not computer.HDD == "null":
            abs_path = os.path.join(computer.HDD, re_path)
            if not os.path.exists(abs_path):
                return abort(404)
            if os.path.isfile(abs_path):
                return send_file(abs_path, as_attachment=("preview" not in request.args))
            dirs, files = CollectFsEntries(abs_path)
            out = "<h2>Markuse kaustad</h2>"
            if platform == "win32":
                out += MakeBreadcrumb("/hdd", abs_path.replace(computer.HDD + ":", ""))
                out += ListDir("/hdd", abs_path.replace(computer.HDD + ":", ""), dirs, files, computer.HDD)
            else:
                out += MakeBreadcrumb("/hdd", abs_path.replace(computer.HDD, "")[1:])
                out += ListDir("/hdd", abs_path.replace(computer.HDD, "")[1:], dirs, files, computer.HDD)
            out += open(maiaroot + "/html_root/upload.html", "r", encoding="UTF-8").read()
            out += open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8").read()
            return render_page_string(out, path=computer.HDD + "/" + re_path)
        else:
            return redirect("/")


@app.route("/images/<path:req_path>")
def dload_img(req_path):
    abs_path = os.path.join(maiaroot, "images", req_path)
    if not os.path.exists(abs_path):
        return abort(404)
    if os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=False)
    dirs, files = CollectFsEntries(abs_path)
    out = "<h2>Failid kaustas /" + req_path + "</h2>"
    fixed_path = "/" + req_path.replace("\\", "/")
    print(fixed_path)
    out += MakeBreadcrumb("/", fixed_path)
    out += ListDir("/", fixed_path, dirs, files, abs_path)
    out += open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8").read()
    return render_page_string(out)

@app.route("/<path:req_path>")
def file(req_path):
    abs_path = os.path.join(maiaroot, req_path)
    if not os.path.exists(abs_path):
        return abort(404)
    if os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=("preview" not in request.args))
    dirs, files = CollectFsEntries(abs_path)
    out = "<h2>Failid kaustas /" + req_path + "</h2>"
    fixed_path = "/" + req_path.replace("\\", "/")
    print(fixed_path)
    out += MakeBreadcrumb("/", fixed_path)
    out += ListDir("/", fixed_path, dirs, files, abs_path)
    out += open(maiaroot + "/html_root/filebrowser.html", "r", encoding="UTF-8").read()
    return render_page_string(out)


@app.route("/vpc", methods=["GET"])
def virtualmachine():
    if not session:
        return redirect("/")
    else:
        return render_page("/html_root/virtualmachine.html")

@app.route("/attach_usb/<id>", methods=["GET"])
def vm_attach(id):
    if not session:
        return redirect("/")
    else:
        os_name = subprocess.check_output("echo $(sudo virsh list --name)", shell=True, text=True)
        os.popen("sh " + root + "/attach.sh " + id + " " + os_name)
        return redirect("/vpc")

@app.route("/detach_usb/<id>", methods=["GET"])
def vm_detach(id):
    if not session:
        return redirect("/")
    else:
        os_name = subprocess.check_output("echo $(sudo virsh list --name)", shell=True, text=True)
        os.popen("sh " + root + "/detach.sh " + id + " " + os_name)
        return redirect("/vpc")

@app.route("/vpc_shutdown", methods=["GET"])
def vm_shutdown():
    if not session:
        return redirect("/")
    else:
        os_name = subprocess.check_output("echo $(sudo virsh list --name)", shell=True, text=True)
        os.popen("sudo virsh shutdown " + os_name)
        return redirect("/vpc")

@app.route("/vpc_reboot", methods=["GET"])
def vm_reboot():
    if not session:
        return redirect("/")
    else:
        os_name = subprocess.check_output("echo $(sudo virsh list --name)", shell=True, text=True)
        os.popen("sudo virsh reboot " + os_name)
        return redirect("/vpc")


@app.route("/vpc_run/<name>", methods=["GET"])
def vm_run(name):
    if not session:
        return redirect("/")
    else:
        os.popen("sudo virsh start " + name)
        return redirect("/vpc")
    
@app.route("/mount_flash", methods=["GET"])
def mount_flash():
    args = request.args
    for i in range(1, 10):
        os.popen("udisksctl mount -b " + args["path"] + str(i))
    return redirect("/")

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    return render_page_string("<h1>Ups, ebaõnn!</h1><p>Midagi läks valesti ja me ei saanud toimingut lõpule viia</p><p>Veakood: " + str(e.code) + "</p>" + "<p>Vea nimetus: " + e.name + "</p><p>Kirjeldus: " + e.description + "</p>")


if __name__ == "__main__":
    app.run(host=serverhost, port=serverport)
