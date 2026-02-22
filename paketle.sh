#!/bin/bash

# Değişkenler
APP_NAME="islami-test"
VERSION="1.0.0"
DEB_DIR="islami-test"
INSTALL_DIR="/opt/$APP_NAME"

echo "--- .deb Paketi Hazırlama İşlemi Başladı ---"

# 1. Temizlik ve Dizin Oluşturma
rm -rf $DEB_DIR
mkdir -p $DEB_DIR/DEBIAN
mkdir -p $DEB_DIR$INSTALL_DIR
mkdir -p $DEB_DIR/usr/bin
mkdir -p $DEB_DIR/usr/share/applications

# 2. Uygulama Dosyalarını Kopyala
echo "Dosyalar kopyalanıyor..."
cp *.py $DEB_DIR$INSTALL_DIR/
cp *.json $DEB_DIR$INSTALL_DIR/
cp *.mp3 $DEB_DIR$INSTALL_DIR/ 2>/dev/null || true
cp icon.png $DEB_DIR$INSTALL_DIR/ 2>/dev/null || true

# 3. Kontrol Dosyası Oluştur (DEBIAN/control)
cat <<EOF > $DEB_DIR/DEBIAN/control
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pyqt6, libqt6multimedia6
Maintainer: mobilturka <github.com/03tekno>
Description: PyQt6 ile hazırlanmış İslami Bilgi Yarışması.
 1400 karma soru ile
EOF

# 4. Başlatıcı Script Oluştur (Bin)
cat <<EOF > $DEB_DIR/usr/bin/$APP_NAME
#!/bin/bash
cd $INSTALL_DIR && python3 islami-test.py
EOF
chmod +x $DEB_DIR/usr/bin/$APP_NAME

# 5. Masaüstü Kısayolu Oluştur (.desktop)
cat <<EOF > $DEB_DIR/usr/share/applications/$APP_NAME.desktop
[Desktop Entry]
Name=İslami Test
Comment=Dini Bilgi Yarışması
Exec=/usr/bin/$APP_NAME
Icon=$INSTALL_DIR/icon.png
Type=Application
Categories=Education;
Terminal=false
EOF

# 6. Python Kodundaki Dosya Yollarını Sabitle (Opsiyonel ama Önemli)
# Kodun içindeki yerel yolları /opt dizinine yönlendirmek için:
# sed -i "s|open('|open('$INSTALL_DIR/|g" $DEB_DIR$INSTALL_DIR/*.py

# 7. İzinleri Ayarla
sudo chown -R root:root $DEB_DIR
sudo chmod -R 755 $DEB_DIR

# 8. Paketi Oluştur
dpkg-deb --build $DEB_DIR

echo "--- İşlem Tamamlandı! ---"
echo "Kurulum için: sudo apt install ./$DEB_DIR.deb"