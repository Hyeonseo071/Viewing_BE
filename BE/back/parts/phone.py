# # phone.py
# from flask import Blueprint, jsonify, request
# from model import PhoneNumber, RandomNick
# from utils import random_nickname
# from app import db 

# phone_bp = Blueprint('phone', __name__)

# @phone_bp.route('/submit-phone', methods=['POST'])
# def submit_phone():
#     data = request.get_json()
#     phone_number = data.get('phoneNumber')

#     if phone_number:
#         ex_phone_number = PhoneNumber.query.filter_by(phone_number=phone_number).first()
#         if ex_phone_number:
#             return jsonify({'nickname': ex_phone_number.nickname}), 200
#         else:
#             nickname = random_nickname()
#             new_phone_number = PhoneNumber(phone_number=phone_number, nickname=nickname)
#             random_nick = RandomNick(phone_number=phone_number, rand_nickname=nickname)
#             try:
#                 db.session.add(new_phone_number)
#                 db.session.add(random_nick)
#                 db.session.commit()
#                 return jsonify({'nickname': nickname}), 200
#             except Exception as e:
#                 db.session.rollback()
#                 return jsonify({'message': 'Error saving phone number', 'error': str(e)}), 500
#     else:
#         return jsonify({'message': 'Phone number is missing'}), 400
