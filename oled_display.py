import time
import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class OledDisplay:
    i2c = None
    disp = None
    width = 0
    height = 0
    top = 0
    bottom = 0
    image = None
    draw = None
    font = None

    def __init__(self):
        # Create the I2C interface.
        self.i2c = busio.I2C(SCL, SDA)

        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new("1", (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Define some constants to allow for easy positioning and resizing of shapes.
        self.padding = -2
        self.top = self.padding
        self.bottom = self.height - self.padding

        # Load font
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 9)

        # Clear image and display
        self.clear()
        self.present()

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def present(self):
        self.disp.image(self.image)
        self.disp.show()

    def drawTextLine(self, x, y, text):
        self.draw.text((x, self.top + y), text, font=self.font, fill=255)

    def drawRectangle(self, x, y, w, h):
        self.draw.rectangle((x, y, x+w, y+h), outline=1, fill=1)

