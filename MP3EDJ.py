#-*- coding: utf-8 -*-
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import uic               # library that allowes the use of .ui GUI from QtDesigner
# resource C:\Python27\Lib\site-packages\PyQt4\pyrcc4.exe -o play_rc.py play.qrc
# compile  pyuic4 -o gui.py MP3EDJ.ui
# from gui import Ui_MainWindow     # compiled GUI
from PyQt4.phonon import Phonon
import sys, os, shutil, subprocess
import time
from mutagen.id3 import ID3,TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, APIC, TBPM,TKEY
from send2trash import send2trash

import sip
sip.setapi('QString', 1)

# TODO
# - Logging
# - Undo: delete, move
# - osx function keys prev, play/pause, next, volume
# - map delete key to “ and eject cd rom key and backspace
# - on delete show msg box for 1 s
# - if strange ascii in filename pop that sucker
# - set currently playing row to red or something
# - delete and move track that is currently playing not the one that is selected
# - config so the user can set language, folders to move files to, logging options
# - drag and drop, export as playlist
# - if key is written in metadata set color based on scale
# - when trying to move, if duplicate display window that displays files attributes to decide witch to keep
# - ? analise key ?
# - switch playing module that can pitch up in real time

# old TODO
# SORT BY KEY
# SORT BY BPM
# BOTH


# GUI +sort key + sort bpm+ both
notCapital = ["1","2","3","4","5","6","7","8","9",
              "01","02","03","04","05","06","07","08","09","10","11","12",
              "1a","2a","3a","4a","5a","6a","7a","8a","9a","10a","11a","12a",
              "1A","2A","3A","4A","5A","6A","7A","8A","9A","10A","11A","12A",
              "1b","2b","3b","4b","5b","6b","7b","8b","9b","10b","11b","12b",
              "1B","2B","3B","4B","5B","6B","7B","8B","9B","10B","11B","12B",
              "(06)", "[06]", " ", "- ", "-",
              "a1", "a2",
              "02","03"]


class EDJ(QMainWindow):
    def __init__(self, parent= None):
        super(EDJ, self).__init__(parent)
        # self.dlg = Ui_MainWindow()
        # self.dlg.setupUi(self)
        self.dlg = uic.loadUi("MP3EDJ.ui")
        self.dlg.show()
        self.dlg.actionMusic.setChecked(True)
        self.dlg.statusbar.showMessage("Izberi datoteke ali mapo")
        self.work= Work()
        self.list=[]
        self.row=""
        self.load()
        self.initialize_connects()

    # CONNECT
    def initialize_connects(self):

        #THREADS SIGNALS
        self.connect(self.work, SIGNAL("threadDone(int,int)"), self.progress)
        self.connect(self.work, SIGNAL("threadDone2(QString)"), self.message)

        #MENUBAR
        QObject.connect(self.dlg.actionMove_all_files_to_root_folder, SIGNAL("triggered()"), self.moveFilesToRoot)
        QObject.connect(self.dlg.actionMove_Files_to_KEY_Sub_Folders, SIGNAL("triggered()"), self.moveFilesToKeySubFolder)
        QObject.connect(self.dlg.actionRename_Files_by_ID3v2_Data, SIGNAL("triggered()"), self.renameFileNames)

        #TOOLBAR
        QObject.connect(self.dlg.actionAdd_Files, SIGNAL("triggered()"), self.file_select)
        QObject.connect(self.dlg.actionAdd_Folder, SIGNAL("triggered()"), self.directory_select)
        QObject.connect(self.dlg.actionMusic, SIGNAL("triggered()"), self.music)
        QObject.connect(self.dlg.actionGenre, SIGNAL("triggered()"), self.genre)
        QObject.connect(self.dlg.actionConverter, SIGNAL("triggered()"), self.convert)
        QObject.connect(self.dlg.actionStretch, SIGNAL("triggered()"), self.stretch)
        QObject.connect(self.dlg.actionPlaylist, SIGNAL("triggered()"), self.playlist)
        QObject.connect(self.dlg.actionSplitter, SIGNAL("triggered()"), self.splitter)
        QObject.connect(self.dlg.actionNormalize, SIGNAL("triggered()"), self.normalize)
        QObject.connect(self.dlg.actionRecorder, SIGNAL("triggered()"), self.recorder)
        QObject.connect(self.dlg.actionEXIT, SIGNAL("triggered()"), self.exit)

        # Audio module
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.player = Phonon.MediaObject(self)

        # PLAYER CONTROL
        self.dlg.seekSlider.setMediaObject(self.player)
        self.player.setTickInterval(1000)
        self.player.tick.connect(self.tick)
        Phonon.createPath(self.player, self.audioOutput)
        self.dlg.volumeSlider.setAudioOutput(self.audioOutput)
        self.player.connect(self.dlg.listWidget,SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.play)
        QObject.connect(self.dlg.actionPlay, SIGNAL("triggered()"), self.play)
        QObject.connect(self.dlg.actionNext, SIGNAL("triggered()"), self.next)
        QObject.connect(self.dlg.actionPrev, SIGNAL("triggered()"), self.back)
        QObject.connect(self.dlg.actionPause, SIGNAL("triggered()"), self.stop)
        QObject.connect(self.player, SIGNAL("finished()"), self.next)

        #MOVE
        QObject.connect(self.dlg.actionTECHNO, SIGNAL("triggered()"), self.mv_techno)
        QObject.connect(self.dlg.actionHardTechno, SIGNAL("triggered()"), self.mv_htechno)
        QObject.connect(self.dlg.actionHardCore, SIGNAL("triggered()"), self.mv_hc)
        QObject.connect(self.dlg.actionDrum_Bass, SIGNAL("triggered()"), self.mv_dnb)
        QObject.connect(self.dlg.actionDelete, SIGNAL("triggered()"), self.brisi)

    #MAIN
    def file_select(self):
        files = QFileDialog.getOpenFileNames(self,
                "QFileDialog.getOpenFileNames()",os.getcwdu(),
                "mp3 Files (*.mp3)")
        if files:
                #self.dlg.listWidget.clear()
                for file in files:
                        filepath, filename = os.path.split(str(file))
                        self.list.append(str(filename))
                        self.dlg.listWidget.addItem(str(filename))
        pass

    def directory_select(self):
        path=QFileDialog.getExistingDirectory()
        if path!="":
            try:
                os.chdir(unicode(str(path)))
                #os.chdir(str(path).encode('utf-8'))
                self.dlg.listWidget.clear()
                self.load()
            except:
                self.message("Znebi se ŠUMNIKOV!")

    def load(self):
        list=[]
        a=0
        i=0
        self.dlg.progressBar.setMinimum(0)
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if os.path.splitext(file)[1]==".mp3" or os.path.splitext(file)[1]==".wav":
                    i+=1
        self.dlg.progressBar.setMaximum(i)
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                a+=1
                self.dlg.progressBar.setValue(a)
                if os.path.splitext(file)[1]==".mp3" or os.path.splitext(file)[1]==".wav":
                    if dirs=="":
                        list.append(file)
                        self.dlg.listWidget.addItem(file)
                    else:
                        list.append(os.path.join(root,file))
                        self.dlg.listWidget.addItem(os.path.join(root,file))
                QApplication.processEvents()
        self.list = list[:]
        if list != 0:
            self.row = 0
            self.dlg.listWidget.setCurrentRow(self.row)
        self.dlg.progressBar.setValue(0)

    def progress(self, current, max):
        self.dlg.progressBar.setValue(current)
        self.dlg.progressBar.setMaximum(max)

    def message(self, text):
        QMessageBox.information(self, "Sporocilo", text)
        self.dlg.progressBar.setValue(0)

    def refresh(self):
        self.dlg.listWidget.clear()
        self.load()
        self.play()

    # TOOL BAR
    def music(self):
        self.dlg.actionGenre.setChecked(False)
        self.dlg.actionMusic.setChecked(True)
        self.dlg.actionTECHNO.setIconText("TECHNO")
        self.dlg.actionHardTechno.setIconText("HardTechno")
        self.dlg.actionHardCore.setIconText("HardCore")
        self.dlg.actionDrum_Bass.setIconText("Drum&Bass")

    def genre(self):
        self.dlg.actionMusic.setChecked(False)
        self.dlg.actionGenre.setChecked(True)
        self.dlg.actionTECHNO.setIconText("     1      ")
        self.dlg.actionHardTechno.setIconText("      2       ")
        self.dlg.actionHardCore.setIconText("      3      ")
        self.dlg.actionDrum_Bass.setIconText("       4      ")

    def convert(self):
        #try:
            self.dlg.actionConverter.setChecked(True)
            filename=self.list[int(self.dlg.listWidget.currentRow())]
            base, ext = os.path.splitext(filename)
            if ext==".mp3":
                self.message(" *.mp3 found,"
                             "converting to *.wav")
                if not os.path.exists("wav"): os.makedirs("wav")
                Work.v_wav(self.work,os.path.join(os.getcwd(),filename),os.path.join(os.getcwd(),"wav",base+".wav"))
            if ext==".wav":
                self.message(" *.wav found,"
                             "converting to *.mp3")
                Work.v_mp3(self.work,os.path.join(os.getcwd(),filename),os.path.join(os.getcwd(),base+"2.mp3"))
            self.dlg.actionConverter.setChecked(False)
            self.directory_select()
            self.dlg.actionConverter.setChecked(False)
            pass

    def stretch(self):
        try:
            self.dlg.actionStretch.setChecked(True)
            filename=self.list[int(self.dlg.listWidget.currentRow())]
            base, ext = os.path.splitext(filename)
            try:
                track=self.read_id3v2(os.path.join(os.getcwd(),filename))
                print(track)
            except:
                if ext!=".mp3":
                    self.message("Make shure you selected \nan *.mp3 file")
                else:
                    self.message("Analyse track  in Traktor:\n"+ filename)
            if ext==".mp3":
                if not os.path.exists("stretch"): os.makedirs("stretch")
                i, ok = QInputDialog.getInteger(self,"QInputDialog.getInteger()", "Percentage:", 160, 120, 300)
                i=str(i)
                if ok:
                    Work.v_wav(self.work,os.path.join(os.getcwd(),filename),os.path.join(os.getcwd(),"stretch",base+".wav"))
                    self.progress(1,4)
                    Work.spremeni_hitrost(self.work,os.path.join(os.getcwd(),"stretch",base+".wav"), os.path.join(os.getcwd(),"stretch",base+".stretch.wav"),track[3],i)
                    os.remove(os.path.join(os.getcwd(),"stretch",base+".wav"))
                    self.progress(2,4)
                    Work.v_mp3(self.work,os.path.join(os.getcwd(),"stretch",base+".stretch.wav"),os.path.join(os.getcwd(),"stretch",base+"."+i+".mp3"))
                    os.remove(os.path.join(os.getcwd(),"stretch",base+".stretch.wav"))
                    self.progress(3,4)
                    try:
                        audio= ID3(os.path.join(os.getcwd(),"stretch",base+"."+i+".mp3"))
                        audio["TPE1"] = TPE1(encoding=3, text=track[0])
                        audio["TIT2"] = TIT2(encoding=3, text=track[1])
                        audio["TKEY"] = TKEY(encoding=3, text=track[2])
                        audio["TBPM"] = TBPM(encoding=3, text=i)
                        audio["COMM"] = COMM(encoding=3, lang=u'eng', desc='desc', text='Stretched with MP3EDJ')
                        audio.save(os.path.join(os.getcwd(),"stretch",base+"."+i+".mp3"), v1=2)
                    except:
                        pass
                    self.list.append(os.path.join("stretch",base+"."+i+".mp3"))
                    self.dlg.listWidget.addItem(os.path.join("stretch",base+"."+i+".mp3"))
                    self.progress(4,4)
            self.dlg.actionStretch.setChecked(False)
            self.dlg.progressBar.setValue(0)
        except:
            pass

    def playlist(self):
        try:
            pass
        except:
            self.directory_select() #Fileselect
            pass

    def splitter(self):
        try:

            Work.run(self.work)
        except:
            self.directory_select() #Fileselect
            pass

    def normalize(self):
        try:
            pass
        except:
            self.directory_select() #Fileselect
            pass

    def recorder(self):
        try:
            pass
        except:
            self.directory_select() #Fileselect
            pass

    def analyse(self):
        #self.work.start()
        Work.run(self.work)
        self.emit(SIGNAL("poslji(QString)"), "DONE")
        #QMessageBox.information(self,"done", "done

    def exit(self):
       sys.exit(1)

    # PLAYER
    def tick(self, time):
        displayTime = QTime(0, (time / 60000) % 60, (time / 1000) % 60)
        self.dlg.lcdNumber.display(displayTime.toString('mm:ss'))

    def play(self):
            # self.dlg.listWidget.setStyleSheet('color: green')
            self.player.setCurrentSource(Phonon.MediaSource(os.path.join(str(os.getcwd()),self.list[int(self.dlg.listWidget.currentRow())])))
            self.player.play()
            self.row=self.dlg.listWidget.currentRow()
            # print(self.list[int(self.dlg.listWidget.currentRow())])
            # t.item(0)->setForeground(Qt::red);
            # self.dlg.listWidget.item(self.row).setForeground("red")
            self.dlg.statusbar.showMessage(self.list[int(self.dlg.listWidget.currentRow())])
            try:
                podatki=self.read_id3v2(self.list[int(self.dlg.listWidget.currentRow())])
                print(podatki)
                self.dlg.Izvajalec.setText(podatki[0])
                self.dlg.Naslov.setText(podatki[1])
                self.dlg.Key.setText(podatki[2])
                self.dlg.BPM.setText(podatki[3])
                # self.dlg.labelLength.setText(podatki[4])
                # print(podatki[4])
                # print(podatki)
            except:
                self.dlg.Izvajalec.setText(self.list[int(self.dlg.listWidget.currentRow())])
                pass

    def next(self):
        try:
            if self.row + 1 < len(self.list):
                self.player.stop()
                self.dlg.lcdNumber.display('00:00')
                self.dlg.listWidget.setCurrentRow(self.row+1)
                self.play()
            else:
                self.player.stop()
                self.dlg.listWidget.setCurrentRow(0)
                self.play()
        except:
            self.message("failed :(")
            pass

    def back(self):
        try:
            if self.row!=0:
                self.player.stop()
                self.dlg.lcdNumber.display('00:00')
                self.dlg.listWidget.setCurrentRow(self.row-1)
                self.play()
        except:
            self.directory_select()
            pass

    def stop(self):
        try:
            self.player.stop()
            self.dlg.lcdNumber.display('00:00')
            self.dlg.statusbar.showMessage("")
        except:
            self.directory_select()
            pass

    # PREMAKNI
    def premakni(self,ponor):
        self.player.stop()
        item=self.list[(self.dlg.listWidget.currentRow())]
        self.player.setCurrentSource(Phonon.MediaSource(""))

        if ponor!=None:
            ponor = str(ponor.replace("/", "\\"))
            ponor = str(ponor.replace(" ", ""))
            if not os.path.exists(ponor): os.makedirs(ponor)
            shutil.move(os.path.join(str(os.getcwd()),item), ponor)
        else:
            send2trash(os.path.join(os.getcwd(),item))
        del self.list[self.dlg.listWidget.currentRow()]
        self.dlg.listWidget.takeItem(self.dlg.listWidget.currentRow())
        if self.row + 1 < len(self.list):
            self.dlg.listWidget.setCurrentRow(self.row)
            self.play()
        else:
            self.player.stop()
            self.dlg.listWidget.setCurrentRow(0)
            if self.dlg.listWidget.currentRow() == -1:
                self.stop()
                self.player.clearQueue()
                self.dlg.Izvajalec.setText("")
                self.dlg.Naslov.setText("")
                self.dlg.Key.setText("")
                self.dlg.BPM.setText("KONEC")
            else:
                self.play()

    def mv_techno(self):

        ponor = self.dlg.actionTECHNO.iconText()
        self.premakni(ponor)

    def mv_htechno(self):
        try:
            ponor = self.dlg.actionHardTechno.iconText()
            self.premakni(ponor)
        except:
            self.directory_select()
            pass

    def mv_dnb(self):
        try:
            ponor = self.dlg.actionDrum_Bass.iconText()
            self.premakni(ponor)
        except:
            self.directory_select()
            pass

    def mv_hc(self):
        try:
            ponor = self.dlg.actionHardCore.iconText()
            self.premakni(ponor)
        except:
            self.directory_select()
            pass

    def brisi(self):
        try:
            if self.dlg.checkBoxBrisi.isChecked():
                self.premakni(None)
            else:
                self.message("Omogoci to moznost !")
        except:
            self.directory_select()
            pass

    def read_id3v2(self,fname):
        audio = ID3(fname)
        data=[]
        #rint(audio['TPE1'].text[0],audio["TIT2"].text[0], audio["TKEY"].text[0], audio["TBPM"].text[0])
        try:
           data.append(audio['TPE1'].text[0])
        except:
           try:
               filepath, filename = os.path.split(fname)
               data.append(filename)
           except:
              data.append(fname)
        try:
           data.append(audio["TIT2"].text[0])
        except:
           data.append("")
        try:
           data.append(audio["TKEY"].text[0])
        except:
           data.append("")
        try:
           data.append(audio["TBPM"].text[0])
        except:
            data.append("")
        return data

    # EDITOR
    def renameFileNames(self):
        self.stop()
        for file in os.listdir(os.getcwd()):
            if file.endswith(".mp3"):
                base, ext = os.path.splitext(file)
                try:
                    data=self.read_id3v2(os.path.join(os.getcwd(),file))
                except:
                    self.message("bad ASCII")
                    continue
                artist = data[0].replace("_", " ")
                artist = artist.replace(":", "-")
                words = artist.split()
                try:
                    while words[0] in notCapital:
                        del words[0]
                except:
                        self.message("Can't rename")
                try:
                    artist = " ".join(words)
                    base=str(artist+" - "+data[1]+ext)
                    print(base)
                    base.replace("*", "_")
                    base.replace("/", " and ")
                    base.capitalize()
                    os.rename(os.path.join(os.getcwdu(),file), os.path.join(os.getcwdu(),base))
                except:
                    self.message("Something went wrong:\n"+file+"\n:(")
                    continue
        self.message("Done editing filenames :)")
        self.refresh()

    def moveFilesToRoot(self):
        here = os.getcwdu()
        for root, dirs, files in os.walk(here, topdown=False ):
            if root != here:
                for name in files:
                    source = os.path.join(root, name)
                    target = self.doubles(os.path.join(here, name), here)
                    os.rename(source, target)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.refresh()

    def doubles(self, target,here):
        base, ext = os.path.split(target)
        count = 0
        while os.path.exists(target):
            count += 1
            target = target + "Double" + str(count) + ext
            self.message(target + "DVOJNIK" + str(count) + ext)
            send2trash(os.path.join(here, target))
        return target

    def moveFilesToKeySubFolder(self):
        self.dlg.progressBar.setMinimum(0)
        for file in os.listdir(os.getcwd()):
            i = 0
            if os.path.splitext(file)[1] == ".mp3" or os.path.splitext(file)[1] == ".wav":
                i += 1
        self.dlg.progressBar.setMaximum(i)
        i = 0
        for file in os.listdir(os.getcwd()):
            if file.endswith(".mp3"):
                i += 1
                self.dlg.progressBar.setValue(i)
                try:
                    dat=self.read_id3v2(os.path.join(os.getcwd(),file))
                    print(dat)
                except:
                    try:
                        if not os.path.exists(os.path.join(os.getcwd(),"unknown")): os.makedirs(os.path.join(os.getcwd(),"unknown"))
                        shutil.move(os.path.join(os.getcwd(),file), os.path.join(os.getcwd(),"unknown"))
                    except:
                        self.dlg.statusbar(file + " needs to have ID3v2 data and it's moved to 'unknown' folder. "
                                                  "Please edit it!")
                        continue
                try:
                    key = dat[2]
                    if key != "":   # key
                        if not os.path.exists(os.path.join(os.getcwd(),key)): os.makedirs(os.path.join(os.getcwd(),key))
                        shutil.move(os.path.join(os.getcwd(),file), os.path.join(os.getcwd(),key))
                except:
                    self.message(file+"is making problems ... please analyse it")
                    try:
                        if not os.path.exists(os.path.join(os.getcwd(),"unknown2")): os.makedirs(os.path.join(os.getcwd(),"unknown2"))
                        shutil.move(os.path.join(os.getcwd(),file), os.path.join(os.getcwd(),"unknown2"))
                        self.dlg.statusbar(file+" needs to have ID3v2 data and it's moved to 'unknown' folder. "
                                                "Please edit it!")
                    except:
                        continue

        self.dlg.progressBar.setValue(0)
        self.refresh()
        self.message("Done moving Files.\n:)")


# WORKER THREAD

class Work(QThread):    # multi thread
    def __init__(self, parent=None):
        super(Work, self).__init__(parent)
        self.pathname, self.scriptname = os.path.split(sys.argv[0])
        
    def run(self):
        j=len(os.listdir(os.getcwd()))
        for i in range(j):
            time.sleep(0.3)
            self.emit(SIGNAL("threadDone(int,int)"), i, j-1)
        self.emit(SIGNAL("threadDone2(QString)"), "DONE")

    def v_mp3(self,file, file2):
        print("v mp3 "+file)
        cmd=[os.path.abspath(self.pathname)+'\\lame\\lame.exe','-b 320','--cbr','-h','--noreplaygain','-q 0',file,file2,'--add-id3v2']
        p = subprocess.call(cmd, shell=False)    # subprocess.PIPE #, stdout=subprocess.PIPE,
                                                 # stderr=subprocess.PIPE universal_newlines=True
        while p.poll() == None:
            # We can do other things here while we wait
            time.sleep(.5)
            p.poll()

    def v_wav(self,file, file2):
        print("v wav"+os.path.join(file))
        cmd = [os.path.abspath(self.pathname)+'\\lame\\lame.exe','--decode','-q 0',file,file2]
        p = subprocess.Popen(cmd,shell=False)   #subprocess.PIPE #, stdout=subprocess.PIPE,  stderr=subprocess.PIPE
        while p.poll() == None:
            # We can do other things here while we wait
            time.sleep(.5)
            p.poll()

    def spremeni_hitrost(self,file,file2,tempo,tempo2):
        print("Track: "+ file)
        print("Stretching tracks bpm: "+tempo+" to: "+tempo2)
        print((float(tempo)/24))
        if tempo != 0:
            cmd = [os.path.abspath(self.pathname)+'\\rubberband-1.8.1-gpl-executable-win32\\rubberband.exe','--tempo',
                   tempo+':'+tempo2, file , file2]
            # cmd=['D:\\USER\\Marko\\Desktop\\rubberband-1.8.1-gpl-executable-win32\\rubberband.exe','--tempo',(tempo)+':'+(tempo2),'-p',chr((tempo)/24), file , file2+'.wav']
            p = subprocess.Popen(cmd, shell=False)
            while p.poll() == None:
                # We can do other things here while we wait
                time.sleep(2)
                p.poll()

        else:
            print("analiziraj :"+file)
            return exit
        print ("STEP 3 !!!!!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = EDJ()
    # form.show()
    app.exec_()

# Functions for windows version

"""    def v_mp3(self,file, file2):
        print("v mp3 "+file)
        cmd=[os.path.abspath(self.pathname)+'\\lame\\lame.exe','-b 320','--cbr','-h','--noreplaygain','-q 0',file,file2,'--add-id3v2']
        subprocess.call(cmd,shell=False) #subprocess.PIPE #, stdout=subprocess.PIPE,  stderr=subprocess.PIPE universal_newlines=True
        print ("KONEC")

    def v_wav(self,file, file2):
        print("v wav"+os.path.join(file))
        cmd=[os.path.abspath(self.pathname)+'\\lame\\lame.exe','--decode','-q 0',file,file2]
        subprocess.call(cmd,shell=False) #subprocess.PIPE #, stdout=subprocess.PIPE,  stderr=subprocess.PIPE

    def spremeni_hitrost(self,file,file2,tempo,tempo2):
        print("Track: "+ file)
        print("Stretching tracks bpm: "+tempo+" to: "+tempo2)
        print((float(tempo)/24))
        if tempo != 0:
            cmd=[os.path.abspath(self.pathname)+'\\rubberband-1.8.1-gpl-executable-win32\\rubberband.exe','--tempo', tempo+':'+tempo2, file , file2]
            #cmd=['D:\\USER\\Marko\\Desktop\\rubberband-1.8.1-gpl-executable-win32\\rubberband.exe','--tempo',(tempo)+':'+(tempo2),'-p',chr((tempo)/24), file , file2+'.wav']
            subprocess.call(cmd, shell=False)

        else:
            print("analiziraj :"+file)
            return exit
        print ("STEP 3 !!!!!")"""