# Imagem do runner self-hosted: a oficial do GitHub, fixada por digest, com o
# que o OpenCV precisa e sem sudo. Construída localmente por runner.sh.
FROM ghcr.io/actions/actions-runner:2.338.2@sha256:6d0b2d80d80f143f77dcb676e50920100bbb547e39e883454d57f45ab8c31300

USER root
# libgl1: o opencv-python (não headless) carrega libGL ao importar o cv2.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 \
 && rm -rf /var/lib/apt/lists/* \
 # Os jobs não precisam de root: tira o runner dos grupos sudo e docker.
 && gpasswd -d runner sudo \
 && gpasswd -d runner docker
USER runner
