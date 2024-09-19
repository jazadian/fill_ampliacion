# Start with the base image
FROM amazon/aws-lambda-python:3.12

RUN dnf install -y atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel nss mesa-libgbm jq unzip
# Copy and run the chrome installer script
COPY ./chrome-installer.sh ./chrome-installer.sh
RUN chmod +x ./chrome-installer.sh
RUN ./chrome-installer.sh
RUN rm ./chrome-installer.sh

# Install Python packages
RUN pip install --upgrade pip
RUN pip install selenium
RUN pip install pymongo
RUN pip install boto3

# Copy application code
COPY lambda_function.py login.py  ./

# Set the command to run the application
CMD ["lambda_function.lambda_handler"]
