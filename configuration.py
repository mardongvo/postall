# -*- coding: utf-8 -*-

import base64

def to_base64(str):
	return base64.b64encode(str.encode()).decode("utf-8")

DB_CONNECTION="host=ip port=5432 dbname=postall user=... password=..." #database path/auth
PROXY_URL="..." #http proxy, set None for no-proxy
#see https://otpravka.pochta.ru/specification#/authorization-token
ACESS_TOKEN	= "....."
LOGIN_PASSWORD	= to_base64("login:pass")
POST_SERVER = "https://otpravka-api.pochta.ru"

#https://otpravka.pochta.ru/specification#/orders-creating_order
#����� ���������� ��������� ��� ��
LETTER_DEFAULT = {
    #"area-to": "", #����� (�����������)
    #"building-to": "", #����� ������: �������� (�����������)
    "comment": "", #�����������:����� ������. ������� ������������� ������, ������� ����������� ������������(�����������)
    #"corpus-to": "", #����� ������: ������ (�����������)
    #"courier": False, #������� '������'  true ��� false (�����������)
    #"dimension": { #�������� ������� (�����������)
    #  "height": 0,
    #  "length": 0,
    #  "width": 0
    #},
    "given-name": "", #��� ����������
    #"hotel-to": "", #�������� ��������� (�����������)
    "house-to": "", #����� ������: ����� ������
    "index-to": 0, #�������� ������ ����� �����
    #"insr-value": 0, #����� ����������� �������� (�������),  (�����������)
    #"letter-to": "string", #����� ������: ������ (�����������)
    #"location-to": "string", #���������� (�����������)
    "mail-category": "ORDERED", #��������� ���: SIMPLE, ORDERED, ORDINARY, WITH_DECLARED_VALUE, WITH_DECLARED_VALUE_AND_CASH_ON_DELIVERY, COMBINED, https://otpravka.pochta.ru/specification#/enums-base-mail-category
    "mass": 0, #��� ��� (� �������)
    #"middle-name": "string", #�������� ���������� (�����������)
    #"num-address-type-to": "string", #����� ��� �/�, ��������� �����, ��������� ����� ��, ������� ����� (�����������)
    "order-num": "", #����� ������. ������� ������������� ������, ������� ����������� ������������, 
    #"payment": 0, #����� ����������� ������� (�������)  (�����������)
    "place-to": "", #���������� �����
    "recipient-name": "", #������������ ���������� ����� ������� (���, ������������ �����������)
    "region-to": "", #�������, ������
    "room-to": "", #����� ������: ����� ��������� (�����������)
    #"slash-to": "string", #����� ������: ����� (�����������)
    #"sms-notice-recipient": 0, #������� ������ SMS ����������� (�����������)
    "street-to": "", #����� ������: �����
    "surname": "", #������� ����������
    #"tel-address": 0, #������� ���������� (����� ���� ������������ ��� ��������� ����� �����������) (�����������)
    #"with-order-of-notice": true, #������� '� �������� ������������' true ��� false (�����������)
    "with-simple-notice": True, #������� '� ������� ������������' (�����������)
    #"wo-mail-rank": true #������� '��� �������' (�����������)
}

#��� ���� ������������� ����������� � �� �������� � ���� �� �������������
#����� ����������� � ��������� ����
LETTER_CONSTANT_FIELDS = {
    "address-type-to": "DEFAULT", #��� ������ DEFAULT, PO_BOX, DEMAND
    "envelope-type": "DL", #��� �������� - ���� � 51506-99. (�����������), https://otpravka.pochta.ru/specification#/enums-base-envelope-type
    "fragile": False, #����������� �� ������� '���������/�������'?,  true ��� false
    "mail-direct": 643, #��� ������ ������: 643
    "mail-type": "LETTER", #��� ���. https://otpravka.pochta.ru/specification#/enums-base-mail-type
    "manual-address-input": True, #������� '������ ���� ������'  true ��� false
    "payment-method": "STAMP", #������ ������  (�����������) CASHLESS,  STAMP, FRANKING https://otpravka.pochta.ru/specification#/enums-payment-methods
    "postoffice-code": "", #������ ����� ������ (�����������)
}

#�������������� ���� ��� ��
LETTER_DB_FIELDS = {
	"letter_id": "sequence", #=integer autoincrement, serial
	"reestr_id": "integer",#
	"id":"integer", #������������� � �����
	"barcode":"text", #���
	"mass_pages", #���������� �������
	"user_id": "text", #������������� ������������
}

#���� ��� �������
REESTR_DB_FIELDS = {
	"reestr_id": "sequence", #=integer autoincrement, serial
	"create_date": "date", #
	"sending_date": "date" #sending-date (�����������) ���� ����� � �������� ��������� (yyyy-MM-dd)
    "with-simple-notice": "boolean", #������� '� ������� ������������' (�����������)
	"user_id": "text", #������������� ������������
}