SiAyank
=================================

Simple Line Bot for class reminder and schedule management


Adding Line Bot
-------------

You can add the bot from the link : https://line.me/R/ti/p/%40977mhifp

or by directly adding by id : @977mhifp

or using a QR Code

.. image:: https://qr-official.line.me/sid/L/977mhifp.png

Requirements
------------

-  Python >= 3.7

Installation
------------

::

    $ pip install -r requirements.txt

Usage
-------------------

**Currently, the bot only supports UGM schedule provided from Simaster.**

Daily reminder will be sent at 06:00 WIB (GMT+7)

-  For some reasons, LINE prohibit users to upload file manually to LINE Official Account. There are 2 known ways to upload your PDF schedule to LINE Official Account :

   -  First, upload the schedule to your LINE Keep storage. Then, upload the PDF to LINE OA from Keep storage. This method works on LINE Desktop version and iOS version.

   -  The second one is by uploading PDF from PDF reader app. Use share feature to directly upload PDF to LINE OA. This method works both on Android and iOS version.



-  List of all class on the same day

::

    /jadwal

-  List of all class

::

    /jadwalAll

-  Move class to other day
   ``/move KODE_MATKUL DAY TIME_BEGIN-TIME_END`` :
::

    /move MII212121 Monday 07:30-09:10

-  Add attendance form
   ``/absen KODE_MATKUL LINK_ABSEN`` :
::

    /absen MII212121 bit.ly/absensi

-  Add meeting link
   ``/meet KODE_MATKUL LINK_MEETING``
::

    /meet MII212121 meet.google.com/abc-defg-hij

-  Remove PDF to turn off reminder 
::
    
    /remove