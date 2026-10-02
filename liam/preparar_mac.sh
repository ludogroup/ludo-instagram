#!/usr/bin/env bash
# Prepara o shell do Cowork no Mac para o LIAM processar vídeos da pasta do Drive.
# Baixa do GitHub só o necessário (scripts, fontes, logos), instala o OpenCV e o detector de rostos.
# Uso (no Mac):  curl -sSfL https://raw.githubusercontent.com/ludogroup/ludo-instagram/main/liam/preparar_mac.sh | bash
set -u
B=https://raw.githubusercontent.com/ludogroup/ludo-instagram/main
D="$HOME/ludo"
mkdir -p "$D/liam" "$D/marca/fontes" "$HOME/.cache/liam-modelos"
for f in liam/midia.py marca/ludo_templates.py marca/logo-branco-transparente.png marca/logo-cinza-transparente.png \
         marca/fontes/manrope-300-normal.ttf marca/fontes/manrope-400-normal.ttf marca/fontes/manrope-500-normal.ttf \
         marca/fontes/manrope-600-normal.ttf marca/fontes/manrope-700-normal.ttf \
         marca/fontes/playfair-display-400-normal.ttf marca/fontes/playfair-display-400-italic.ttf; do
  curl -sSfL --retry 2 -o "$D/$f" "$B/$f" || { echo "ERRO ao baixar $f"; exit 1; }
done
python3 -c "import cv2" 2>/dev/null || python3 -m pip install -q --user opencv-python-headless 2>/dev/null \
  || python3 -m pip install -q --user --break-system-packages opencv-python-headless
python3 -c "import numpy, PIL, cv2; print('python ok: numpy', numpy.__version__, '| pillow', PIL.__version__, '| opencv', cv2.__version__)"
Y="$HOME/.cache/liam-modelos/face_detection_yunet_2023mar.onnx"
[ -s "$Y" ] || curl -sSfL --retry 2 -o "$Y" \
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx \
  || { rm -f "$Y"; echo "aviso: YuNet indisponível, o detector Haar será usado"; }
ffmpeg -hide_banner -filters 2>/dev/null | grep -qE " (subtitles|zscale) " && echo "ffmpeg ok" || echo "aviso: ffmpeg sem libass/zscale"
echo "PRONTO: python3 $D/liam/midia.py"
