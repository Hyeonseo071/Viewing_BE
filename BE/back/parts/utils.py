# import random
# import string
# from model import PhoneNumber

# #랜덤닉네임 함수
# def random_nickname():
#     while True:
#         rand_nick = ''.join(random.choices(string.ascii_uppercase, k=4))
#         if not PhoneNumber.query.filter_by(nickname=rand_nick).first():
#             return rand_nick