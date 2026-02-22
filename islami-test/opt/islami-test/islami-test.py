import sys
import random
import json
import os
import glob

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QProgressBar, QFrame, QGridLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class IslamiTestUygulamasi(QWidget):
    def __init__(self):
        super().__init__()
        self.questions = []
        self.all_data = {} 
        self.current_q = 0
        self.score_correct = 0
        self.score_wrong = 0
        self.max_time = 60
        self.time_left = self.max_time
        self.is_muted = False
        self.current_category = ""
        
        # AYAR DOSYASI YOLU (Home dizininde gizli bir klasör)
        self.save_dir = os.path.join(os.path.expanduser("~"), ".islami_test")
        self.save_file = os.path.join(self.save_dir, "settings.json")
        
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        # SES MOTORU
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        # RENK PALETLERİ
        self.day_style = {
            "bg": "#e0e0e0", "card": "#ffffff", "text": "#2d3436", 
            "accent": "#7f8c8d", "btn": "#f5f5f5", "border": "#bdc3c7"
        }
        self.night_style = {
            "bg": "#2d3436", "card": "#353b48", "text": "#f5f6fa", 
            "accent": "#00b894", "btn": "#485460", "border": "#00b894"
        }

        self.load_all_categories()
        self.init_ui()
        self.apply_theme(self.day_style)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # Uygulama açıldığında kaldığı yeri kontrol et
        QTimer.singleShot(100, self.check_saved_state)

    def center_on_screen(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def load_all_categories(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_files = glob.glob(os.path.join(current_dir, "*.json"))
        
        temp_data = {}
        for file_path in json_files:
            if "settings.json" in file_path: continue 
            try:
                category_name = os.path.basename(file_path).replace(".json", "").capitalize()
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        temp_data[category_name] = data
            except: continue
        
        self.all_data = dict(sorted(temp_data.items()))

    def save_state(self):
        state = {
            "category": self.current_category,
            "current_index": self.current_q,
            "correct": self.score_correct,
            "wrong": self.score_wrong
        }
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except: pass

    def check_saved_state(self):
        """Kaldığı yeri kontrol eder ve TÜRKÇE butonlu mesaj kutusu gösterir."""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                if state["category"] in self.all_data:
                    # Mesaj kutusunu özelleştiriyoruz
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Devam Et")
                    msg_box.setText(f"'{state['category']}' kategorisinde kaldığınız yerden (Soru {state['current_index']+1}) devam etmek ister misiniz?")
                    
                    # Türkçe butonlar ekliyoruz
                    evet_button = msg_box.addButton("Evet", QMessageBox.ButtonRole.YesRole)
                    hayir_button = msg_box.addButton("Hayır", QMessageBox.ButtonRole.NoRole)
                    msg_box.setDefaultButton(evet_button)
                    
                    msg_box.exec()
                    
                    if msg_box.clickedButton() == evet_button:
                        self.current_category = state["category"]
                        self.questions = list(self.all_data[self.current_category])
                        self.current_q = state["current_index"]
                        self.score_correct = state["correct"]
                        self.score_wrong = state["wrong"]
                        self.lbl_correct.setText(f"Doğru: {self.score_correct}")
                        self.lbl_wrong.setText(f"Yanlış: {self.score_wrong}")
                        self.stack.setCurrentIndex(1)
                        self.load_question()
            except: pass

    def start_category(self, category_name):
        self.current_category = category_name
        self.questions = list(self.all_data[category_name])
        random.shuffle(self.questions)
        self.current_q = 0
        self.score_correct = 0
        self.score_wrong = 0
        self.lbl_correct.setText("Doğru: 0")
        self.lbl_wrong.setText("Yanlış: 0")
        
        self.save_state() 
        self.stack.setCurrentIndex(1)
        self.load_question()

    def init_ui(self):
        self.setWindowTitle('İslami Bilgi Yarışması')
        self.setFixedSize(650, 720)
        self.center_on_screen()
        
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        
        # --- EKRAN 1: KATEGORİ SEÇİMİ ---
        self.category_widget = QWidget()
        cat_layout = QVBoxLayout(self.category_widget)
        cat_layout.setContentsMargins(30, 40, 30, 40)
        
        cat_title = QLabel("Lütfen Bir Kategori Seçin")
        cat_title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        cat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_layout.addWidget(cat_title)
        cat_layout.addSpacing(40)
        
        self.cat_grid = QGridLayout()
        self.cat_grid.setSpacing(15)
        
        row, col = 0, 0
        for cat_name in self.all_data.keys():
            btn = QPushButton(cat_name)
            btn.setMinimumHeight(85)
            btn.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, name=cat_name: self.start_category(name))
            self.cat_grid.addWidget(btn, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        cat_layout.addLayout(self.cat_grid)
        cat_layout.addStretch()
        
        # --- EKRAN 2: YARIŞMA EKRANI ---
        self.game_widget = QWidget()
        game_layout = QVBoxLayout(self.game_widget)
        
        top_box = QHBoxLayout()
        self.btn_mute = QPushButton("🔊 Ses Açık")
        self.btn_mute.setFixedWidth(130)
        self.btn_mute.clicked.connect(self.toggle_sound)
        self.btn_back = QPushButton("⬅ Geri")
        self.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.btn_day = QPushButton("☀️")
        self.btn_day.clicked.connect(lambda: self.apply_theme(self.day_style))
        self.btn_night = QPushButton("🌙")
        self.btn_night.clicked.connect(lambda: self.apply_theme(self.night_style))
        
        top_box.addWidget(self.btn_back)
        top_box.addWidget(self.btn_mute)
        top_box.addStretch()
        top_box.addWidget(self.btn_day)
        top_box.addWidget(self.btn_night)
        game_layout.addLayout(top_box)

        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("statsPanel")
        stats_layout = QHBoxLayout(self.stats_frame)
        self.lbl_correct = QLabel("Doğru: 0")
        self.lbl_correct.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        self.lbl_timer = QLabel(f"⏱ {self.max_time}")
        self.lbl_timer.setFont(QFont('Segoe UI', 22, QFont.Weight.Black))
        self.lbl_wrong = QLabel("Yanlış: 0")
        self.lbl_wrong.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.lbl_correct)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lbl_timer)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lbl_wrong)
        game_layout.addWidget(self.stats_frame)

        self.lbl_count = QLabel("")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        game_layout.addWidget(self.lbl_count)
        
        self.pbar = QProgressBar()
        self.pbar.setMaximum(self.max_time)
        self.pbar.setValue(self.max_time)
        self.pbar.setTextVisible(False)
        game_layout.addWidget(self.pbar)

        self.lbl_question = QLabel("")
        self.lbl_question.setObjectName("questionBox")
        self.lbl_question.setFont(QFont('Segoe UI', 15))
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question.setMinimumHeight(180)
        game_layout.addWidget(self.lbl_question)

        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        self.buttons = []
        for i in range(4):
            btn = QPushButton("")
            btn.setFont(QFont('Segoe UI', 11))
            btn.setMinimumHeight(65)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.check_answer)
            self.grid.addWidget(btn, i // 2, i % 2)
            self.buttons.append(btn)
        game_layout.addLayout(self.grid)

        self.stack.addWidget(self.category_widget)
        self.stack.addWidget(self.game_widget)
        self.main_layout.addWidget(self.stack)

    def apply_theme(self, theme):
        self.current_theme = theme
        style = f"""
            QWidget {{ background-color: {theme['bg']}; color: {theme['text']}; }}
            #questionBox {{
                background-color: {theme['card']};
                border-radius: 20px;
                padding: 25px;
                border: 2px solid {theme['accent']};
            }}
            QPushButton {{
                background-color: {theme['btn']};
                border: 1px solid {theme['border']};
                border-radius: 10px;
                color: {theme['text']};
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme['accent']};
                color: {theme['bg']};
            }}
            QProgressBar {{
                border: none;
                background-color: {theme['btn']};
                height: 8px;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 4px;
            }}
        """
        self.setStyleSheet(style)

    def load_question(self):
        if self.current_q < len(self.questions):
            self.save_state() 
            self.time_left = self.max_time
            self.pbar.setValue(self.max_time)
            self.timer.start(1000)
            q_data = self.questions[self.current_q]
            self.lbl_count.setText(f"Soru: {self.current_q + 1} / {len(self.questions)}")
            self.lbl_timer.setText(f"⏱ {self.time_left}")
            self.lbl_question.setText(q_data["soru"])
            opts = list(q_data["siklar"])
            random.shuffle(opts)
            for i, btn in enumerate(self.buttons):
                btn.setText(opts[i])
                btn.setEnabled(True)
                btn.setStyleSheet("") 
        else:
            self.show_result()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.pbar.setValue(self.time_left)
            self.lbl_timer.setText(f"⏱ {self.time_left}")
        else:
            self.timer.stop()
            self.score_wrong += 1
            self.lbl_wrong.setText(f"Yanlış: {self.score_wrong}")
            self.play_sound("wrong")
            self.highlight_correct_answer()
            QTimer.singleShot(1500, self.next_question)

    def check_answer(self):
        self.timer.stop()
        sender = self.sender()
        correct_answer = self.questions[self.current_q]["cevap"]

        if sender.text() == correct_answer:
            sender.setStyleSheet("background-color: #27ae60; color: white; border: none;")
            self.score_correct += 1
            self.lbl_correct.setText(f"Doğru: {self.score_correct}")
            self.play_sound("correct")
        else:
            sender.setStyleSheet("background-color: #c0392b; color: white; border: none;")
            self.score_wrong += 1
            self.lbl_wrong.setText(f"Yanlış: {self.score_wrong}")
            self.play_sound("wrong")
            self.highlight_correct_answer()

        for btn in self.buttons: btn.setEnabled(False)
        QTimer.singleShot(1500, self.next_question)

    def highlight_correct_answer(self):
        ans = self.questions[self.current_q]["cevap"]
        for btn in self.buttons:
            if btn.text() == ans:
                btn.setStyleSheet("background-color: #27ae60; color: white; border: none;")

    def next_question(self):
        self.current_q += 1
        self.load_question()

    def toggle_sound(self):
        self.is_muted = not self.is_muted
        self.btn_mute.setText("🔈 Ses Kapalı" if self.is_muted else "🔊 Ses Açık")
        self.audio_output.setMuted(self.is_muted)

    def play_sound(self, result):
        if self.is_muted: return
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = "correct.mp3" if result == "correct" else "wrong.mp3"
        full_path = os.path.join(current_dir, file_name)
        if os.path.exists(full_path):
            self.media_player.setSource(QUrl.fromLocalFile(full_path))
            self.media_player.play()

    def show_result(self):
        self.timer.stop()
        total = len(self.questions)
        success = int((self.score_correct / total) * 100) if total > 0 else 0
        QMessageBox.information(self, "Sonuç", f"Kategori Bitti!\n\nDoğru: {self.score_correct}\nYanlış: {self.score_wrong}\nBaşarı: %{success}")
        
        if os.path.exists(self.save_file):
            try: os.remove(self.save_file)
            except: pass
            
        self.stack.setCurrentIndex(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = IslamiTestUygulamasi()
    window.show()
    sys.exit(app.exec())