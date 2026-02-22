import sys
import random
import json
import os
import glob

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QProgressBar, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QScreen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class IslamiTestUygulamasi(QWidget):
    def __init__(self):
        super().__init__()
        self.questions = []
        self.current_q = 0
        self.score_correct = 0
        self.score_wrong = 0
        self.max_time = 60 # Süre sınırı 60 saniye olarak belirlendi
        self.time_left = self.max_time
        self.is_muted = False
        
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

        self.load_questions_from_json()
        self.init_ui()
        self.apply_theme(self.day_style)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        if self.questions:
            self.load_question()

    def toggle_sound(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.btn_mute.setText("🔈 Ses Kapalı")
            self.audio_output.setMuted(True)
        else:
            self.btn_mute.setText("🔊 Ses Açık")
            self.audio_output.setMuted(False)

    def play_sound(self, result):
        if self.is_muted: return
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = "correct.mp3" if result == "correct" else "wrong.mp3"
        full_path = os.path.join(current_dir, file_name)
        if os.path.exists(full_path):
            self.media_player.setSource(QUrl.fromLocalFile(full_path))
            self.media_player.play()

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
            #statsPanel {{
                background-color: transparent;
                border: none;
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

    def load_questions_from_json(self):
        all_questions = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_files = glob.glob(os.path.join(current_dir, "*.json"))
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        valid_questions = [q for q in data if "soru" in q and "cevap" in q]
                        all_questions.extend(valid_questions)
            except: continue
        if not all_questions:
            self.questions = [{"soru": "Soru dosyası bulunamadı!", "cevap": "Tamam", "siklar": ["Tamam", "Hata", "Yok", "Kontrol Et"]}]
        else:
            self.questions = all_questions
            random.shuffle(self.questions)

    def center_on_screen(self):
        # Ekranın merkez koordinatlarını hesaplar ve pencereyi oraya taşır
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        self.setWindowTitle('İslami Bilgi Yarışması')
        self.setFixedSize(650, 680)
        self.center_on_screen() # Pencereyi merkeze al
        
        layout = QVBoxLayout()
        layout.setContentsMargins(35, 25, 35, 35)
        layout.setSpacing(15)

        top_box = QHBoxLayout()
        self.btn_mute = QPushButton("🔊 Ses Açık")
        self.btn_mute.setFixedWidth(130)
        self.btn_mute.clicked.connect(self.toggle_sound)
        self.btn_day = QPushButton("☀️ Gündüz")
        self.btn_day.clicked.connect(lambda: self.apply_theme(self.day_style))
        self.btn_night = QPushButton("🌙 Gece")
        self.btn_night.clicked.connect(lambda: self.apply_theme(self.night_style))
        top_box.addWidget(self.btn_mute)
        top_box.addStretch()
        top_box.addWidget(self.btn_day)
        top_box.addWidget(self.btn_night)
        layout.addLayout(top_box)

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
        layout.addWidget(self.stats_frame)

        self.lbl_count = QLabel(f"Soru: 1 / {len(self.questions)}")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_count)
        
        self.pbar = QProgressBar()
        self.pbar.setMaximum(self.max_time)
        self.pbar.setValue(self.max_time)
        self.pbar.setTextVisible(False)
        layout.addWidget(self.pbar)

        self.lbl_question = QLabel("")
        self.lbl_question.setObjectName("questionBox")
        self.lbl_question.setFont(QFont('Segoe UI', 15))
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_question.setMinimumHeight(180)
        layout.addWidget(self.lbl_question)

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
        layout.addLayout(self.grid)

        self.setLayout(layout)

    def load_question(self):
        if self.current_q < len(self.questions):
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

    def show_result(self):
        self.timer.stop()
        total = len(self.questions)
        success = int((self.score_correct / total) * 100) if total > 0 else 0
        msg = QMessageBox(self)
        msg.setWindowTitle("Sonuç")
        msg.setText(f"Test Bitti!\n\nDoğru: {self.score_correct}\nYanlış: {self.score_wrong}\nBaşarı: %{success}")
        msg.exec()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = IslamiTestUygulamasi()
    window.show()
    sys.exit(app.exec())