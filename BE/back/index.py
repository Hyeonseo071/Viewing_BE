from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import random, string, requests
from datetime import datetime

plus = 100
minus = 50
q_score = 0 
results_cache = {}

app = Flask(__name__)

# CORS 설정
cors = CORS(app, supports_credentials=True)

# DB 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/viewinging'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# DB 모델 정의
class PhoneNumber(db.Model):  # 폰번호
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(13), unique=True)
    nickname = db.Column(db.String(4), unique=True)
    trash_counts = db.relationship('TrashCount', backref='phone_number', lazy=True)
    compare_results = db.relationship('CompareResult', backref='phone_number', lazy=True)
    last_update = db.Column(db.DateTime, default=datetime.utcnow) #마지막 업데이트 시간
    def __repr__(self):
        return f'<PhoneNumber {self.phone_number}>'
class RandomNick(db.Model): #랜덤 닉네임(영문4)
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(13), unique=True)
    rand_nickname = db.Column(db.String(4))
    def __repr__(self):
        return f'<RandomNick {self.rand_nickname}>'
class AutoValue(db.Model):  #자동/수동 여부
    id = db.Column(db.Integer, primary_key = True)
    auto_value = db.Column(db.String(13))

    def __repr__(self):
        return f'<AutoValue {self.auto_value}>'
class TrashCount(db.Model):  # 쓰레기 종류/갯수
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(4), db.ForeignKey('phone_number.nickname'))
    plastic_count = db.Column(db.Float, default=0.0)
    vinyl_count = db.Column(db.Float, default=0.0)
    can_count = db.Column(db.Float, default=0.0)
    general_count = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<TrashCount {self.nickname} - Plastic: {self.plastic_count}, Vinyl: {self.vinyl_count}, Can: {self.can_count}, General: {self.general_count}>'
    
class Trash(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trash = db.Column(db.String(15))

    def __repr__(self):
        return f'<Trash {self.trash}>'
class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(15))

    def __repr__(self):
        return f'<Label {self.label}>'
class CompareResult(db.Model):  # 비교값
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.String(10))
    score = db.Column(db.Integer)
    nickname = db.Column(db.String(4), db.ForeignKey('phone_number.nickname'))
    solution = db.Column(db.String(255))

    def __repr__(self):
        return f'<CompareResult {self.result} - {self.score} - {self.nickname}>'
class UserLog(db.Model): # 사용자 로그인 기록
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), db.ForeignKey('phone_number.phone_number'))
    login_time = db.Column(db.DateTime, default=db.func.now())
    login_count = db.Column(db.Integer, default=1)

def random_nickname():#랜덤닉네임 함수
    while True:
        rand_nick = ''.join(random.choices(string.ascii_uppercase, k=4))
        if not PhoneNumber.query.filter_by(nickname=rand_nick).first():
            return rand_nick

#전화번호제출
@app.route('/submit-phone', methods=['POST'])
def submit_phone():
    data = request.get_json()
    phone_number = data.get('phoneNumber')

    if not phone_number:
        return jsonify({'message': 'Phone number is missing'}), 400

    # 기존 사용자 확인
    ex_phone_number = PhoneNumber.query.filter_by(phone_number=phone_number).first()

    if ex_phone_number:
        # 기존 사용자의 로그인 기록 업데이트
        user_log = UserLog.query.filter_by(phone_number=phone_number).first()
        if user_log:
            user_log.login_count += 1
            user_log.login_time = datetime.now()  # 최신 로그인 시간 갱신
        else:
            # 첫 로그인 기록 생성
            user_log = UserLog(phone_number=phone_number, login_time=datetime.now(), login_count=1)
            db.session.add(user_log)

        db.session.commit()

        # 닉네임 반환
        return jsonify({'nickname': ex_phone_number.nickname}), 200
    else:
        # 새 사용자: 전화번호 저장 및 닉네임 생성
        nickname = random_nickname()
        new_phone_number = PhoneNumber(phone_number=phone_number, nickname=nickname)

        # 로그인 기록 생성
        user_log = UserLog(phone_number=phone_number, login_time=datetime.now(), login_count=1)

        try:
            db.session.add(new_phone_number)
            db.session.add(user_log)
            db.session.commit()
            return jsonify({'nickname': nickname}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Error saving phone number', 'error': str(e)}), 500

# 랜덤 닉네임 가져가기
@app.route('/get-random-nickname/<string:phone_number>', methods=['GET'])
def get_random_nickname(phone_number):
    random_nick = RandomNick.query.filter_by(phone_number=phone_number).first()
    if random_nick:
        return jsonify({'rand_nickname': random_nick.rand_nickname}), 200
    else:
        return jsonify({'message': 'Nickname not found'}), 404

# 수동/자동 여부
@app.route('/auto-signal', methods=['POST'])
def auto_value():
    data = request.get_json()
    auto_value = data.get('auto-signal')

    if auto_value:
        try:
            # 기존 값 삭제
            existing_value = AutoValue.query.filter_by(auto_value=auto_value).first()
            if existing_value:
                db.session.delete(existing_value)  # 기존 값 삭제

            # 새로운 값 저장
            new_auto_value = AutoValue(auto_value=auto_value)
            db.session.add(new_auto_value)
            db.session.commit()

            # Raspberry Pi로 값 전송
            raspberry_url = "http://10.150.150.80:5000/receive-autovalue"
            try:
                response = requests.post(raspberry_url, json={"auto_value": auto_value})
                response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킴
            except requests.exceptions.RequestException as e:
                # Raspberry Pi로 전송 실패 시 무시하고 계속 진행
                print(f"Failed to send to Raspberry Pi: {str(e)}")

            return jsonify({'message': f"{auto_value} saved successfully and sent to Raspberry Pi"}), 200
        
        except Exception as e:
            db.session.rollback()  # 데이터베이스 트랜잭션 롤백
            return jsonify({'message': f"Error saving the value: {str(e)}"}), 400
    
    else:
        return jsonify({'message': 'Auto value is missing'}), 400

#라즈베리파이로부터 자동: 종류 및 개수
@app.route('/auto-trash', methods=['POST'])
def auto_trash():
    data = request.json 
    label = data.get('label')

    # 가장 최근 `login_count` 증가 사용자 찾기
    user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()
    if not user_log:
        return jsonify({'message': 'No user log found'}), 404

    # phone_number가 없는 경우 예외 처리
    user_nickname = PhoneNumber.query.filter_by(phone_number=user_log.phone_number).first()
    if not user_nickname:
        return jsonify({'message': 'User not found in PhoneNumber table'}), 404

    user_nickname = user_nickname.nickname

    # TrashCount 레코드가 존재하는지 확인
    trash_count = TrashCount.query.filter_by(nickname=user_nickname).first()

    # TrashCount 레코드가 없다면 새로 생성
    if not trash_count:
        trash_count = TrashCount(nickname=user_nickname)
        db.session.add(trash_count)  # 새로 추가

    # 필드 값 증가 처리 (None일 경우 0으로 초기화)
    if label == 'plastic':
        trash_count.plastic_count = (trash_count.plastic_count or 0) + 1
    elif label == 'vinyl':
        trash_count.vinyl_count = (trash_count.vinyl_count or 0) + 1
    elif label == 'can':
        trash_count.can_count = (trash_count.can_count or 0) + 1
    elif label == 'general':
        trash_count.general_count = (trash_count.general_count or 0) + 1

    # 데이터베이스에 변경 사항 반영
    db.session.commit()

    return jsonify({"message": "Trash count updated successfully!"}), 200




def translate_trash(trash):
    # 한국어 쓰레기 값들을 영어로 매핑
    trash_translation = {
        '플라스틱': 'plastic',
        '비닐': 'vinyl',
        '캔': 'can',
        '일반': 'general'
    }
    # 쓰레기 값이 한국어로 들어오면 영어로 변환
    return trash_translation.get(trash)

@app.route('/label', methods=['POST'])
def compare_with_data():
    data = request.get_json()

    trash = data.get('trash')
    label = data.get('label')

    # 임시 저장된 데이터 가져오기
    temp_trash = Trash.query.first()
    temp_label = Label.query.first()

    # 요청 상태 플래그
    is_first_request = not (temp_trash and temp_label)  # 두 데이터가 모두 없는 경우 첫 번째 요청

    # trash가 먼저 들어온 경우
    if trash and not temp_trash:
        translated_trash = translate_trash(trash)
        if translated_trash:
            temp_trash = Trash(trash=translated_trash)
            db.session.add(temp_trash)
            db.session.commit()
            return jsonify({'message': 'Trash value received, awaiting label value'}), 200
        else:
            return jsonify({'message': 'Invalid trash type'}), 400

    # label이 먼저 들어온 경우
    if label and not temp_label:
        temp_label = Label(label=label)
        db.session.add(temp_label)
        db.session.commit()
        return jsonify({'message': 'Label value received, awaiting trash value'}), 200

    # trash와 label 모두 존재하는 경우
    if temp_trash and temp_label:
        translated_trash = temp_trash.trash.strip().lower()  # 공백 제거 및 소문자로 변경
        temp_label_value = temp_label.label.strip().lower()  # 공백 제거 및 소문자로 변경

        print(f"Translated Trash: {translated_trash}")
        print(f"Temp Label: {temp_label_value}")

        # 비교
        if translated_trash == temp_label_value:
            result = 'Right'
            total_score = 100 if is_first_request else 50  # 첫 번째 요청 100점, 이후 50점
        else:
            result = 'Wrong'
            total_score = 50 if is_first_request else 25  # 첫 번째 요청 50점, 이후 25점

        # 가장 최근 `login_count` 증가 사용자 찾기
        user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()
        if not user_log:
            return jsonify({'message': 'No user log found'}), 404

        user_nickname = PhoneNumber.query.filter_by(phone_number=user_log.phone_number).first().nickname

        # 해당 사용자의 `TrashCount` 가져오기
        trash_count = TrashCount.query.filter_by(nickname=user_nickname).first()
        if not trash_count:
            trash_count = TrashCount(nickname=user_nickname)
            db.session.add(trash_count)

        # 쓰레기 종류별 카운트 업데이트
        increment_value = 1 if is_first_request else 0.5  # 첫 번째 요청 1, 이후 0.5

        if result == 'Right':
            trash_type = translated_trash
        else:
            trash_type = temp_label_value

        # 상태 출력으로 확인
        print(f"Before update: {trash_count.plastic_count}, {trash_count.vinyl_count}, {trash_count.can_count}, {trash_count.general_count}")

        if trash_type == 'plastic':
            trash_count.plastic_count = (trash_count.plastic_count or 0) + increment_value
        elif trash_type == 'vinyl':
            trash_count.vinyl_count = (trash_count.vinyl_count or 0) + increment_value
        elif trash_type == 'can':
            trash_count.can_count = (trash_count.can_count or 0) + increment_value
        elif trash_type == 'general':
            trash_count.general_count = (trash_count.general_count or 0) + increment_value

        # 상태 출력으로 확인
        print(f"After update: {trash_count.plastic_count}, {trash_count.vinyl_count}, {trash_count.can_count}, {trash_count.general_count}")

        # 기존 CompareResult 값 가져오기
        existing_result = CompareResult.query.filter_by(nickname=user_nickname).first()

        if existing_result:
            # 기존 점수와 새로운 점수를 합산
            existing_result.score += total_score
            existing_result.result = result
        else:
            # 새로운 CompareResult 추가
            compare_result = CompareResult(
                result=result,
                score=total_score,
                nickname=user_nickname
            )
            db.session.add(compare_result)

        db.session.commit()

        counts = {
            'plastic': trash_count.plastic_count,
            'vinyl': trash_count.vinyl_count,
            'can': trash_count.can_count,
            'general': trash_count.general_count
        }

        return jsonify({
            'result': result,
            'score': existing_result.score if existing_result else total_score,
            'trash_counts': counts
        }), 200

    return jsonify({'message': 'Waiting for both trash and label values'}), 400





@app.route('/get-user-score', methods=['GET'])
def get_user_score():
    # 가장 최근 로그인한 사용자 찾기
    user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()
    if not user_log:
        return jsonify({'message': 'No user log found'}), 404

    # 해당 사용자의 닉네임 찾기
    user_nickname = PhoneNumber.query.filter_by(phone_number=user_log.phone_number).first().nickname

    # 해당 사용자의 CompareResult 찾기
    compare_result = CompareResult.query.filter_by(nickname=user_nickname).first()
    if not compare_result:
        return jsonify({'message': 'No score found for the user'}), 404

    # 점수 반환
    return jsonify({'nickname': user_nickname, 'score': compare_result.score}), 200


@app.route('/compare', methods=['POST'])
def compare_result():
    # 클라이언트로부터 데이터 받기
    data = request.get_json()
    question_num = data.get('questionnum')
    user_answer = data.get('useranswer')

    # 필수 값이 없는 경우 오류 응답
    if question_num is None or user_answer is None:
        return jsonify({'message': 'Question number or answer is missing'}), 400
    
    correct_answers = {
        1: [2],
        2: [1],
        3: [3],
        4: [4],
        6: [1],
        7: [4],
        8: [2],
        9: [1],
        11: [1],
        12: [3],
        13: [1],
        14: [3],
        15: [4],
        17: [1],
        18: [1],
        19: [4],
        20: [2],
        21: [2],
        22: [4],
        25: [1],
        26: [1],
        28: [1],
        29: [4],
        30: [1],
        31: [1],
        32: [1],
        33: [4],
        34: [2],
        35: [4],
        36: [3],
        37: [3],
        38: [2],
        39: [1],
        40: [3],
        42: [1],
        43: [1],
        46: [1],
        48: [1],
        49: [1],
        50: [3]
    }
    solution = {
        1: '택배 상자는 깨끗한 상태라면 종이류로 분리 배출 가능합니다.',
        2: '음식물 얼룩이 있는 피자 박스는 재활용이 불가능하므로 일반쓰레기로 배출해야 합니다.',
        3: '플라스틱 물병은 플라스틱류로 배출해야 하며, 내용물은 비우고 뚜껑은 따로 처리하는 것이 좋습니다.',
        4: '과자 봉지는 비닐류에 해당합니다.',
        6: '일회용 종이컵은 내부 코팅이 되어 있어 재활용이 어렵기 때문에 일반쓰레기로 처리해야 합니다.',
        7: '빵을 포장하는 비닐은 이물질과 스티커를 제거하면 비닐류로 분리배출 할 수 있습니다.',
        8: '신문지는 종이에 포함되므로 종이류로 분리배출해야 합니다.',
        9: '우유 팩은 내부가 플라스틱 코팅되어 있어 재활용이 어려워 일반쓰레기로 배출해야 합니다.',
        11: '플라스틱 칫솔은 다른 재질이 혼합되어 있어 일반쓰레기로 배출해야 합니다.',
        12: '플라스틱으로 만들어진 커피컵 뚜껑은 플라스틱류로 분리배출해야 합니다.',
        13: '감자칩 통(프링글스)은 여러 재질이 혼합되어 있어 일반쓰레기로 배출해야 합니다.',
        14: '플라스틱 장난감은 플라스틱류으로 분리배출해야 합니다.',
        15: '쓰레기봉투는 비닐류로 분류됩니다.',
        17: '플라스틱 옷걸이는 재활용되지 않기 때문에 일반쓰레기로 처리해야 합니다.',
        18: '종이영수증은 열에 의해 인쇄된 화학성분이 포함되어 있어 일반쓰레기로 배출해야 합니다.',
        19: '이물질이 묻은 비닐 장갑은 재활용되지 않기 때문에 일반쓰레기로 배출해야 합니다.',
        20: '종이컵 홀더는 재활용되기 용이한 소재이기에 종이류로 분리배출됩니다.',
        21: '깨끗한 종이로 된 시리얼 박스는 종이류로 분리배출할 수 있습니다.',
        22: '햄버거 포장용 비닐은 비닐류로 분리배출해야 합니다.',
        25: '커피 찌꺼기를 담은 종이 봉투는 일반쓰레기로 분리배출할 수 있습니다.',
        26: '소금과 후추를 담은 비닐 봉지는 일반쓰레기로 분리배출해야 합니다.',
        28: '플라스틱 클립은 재활용이 되지 않아 일반쓰레기로 처리해야 합니다.',
        29: '비닐 식품 포장지는 비닐류로 분리배출해야 합니다.',
        30: '사용된 종이 타올은 재활용이 어려워 일반쓰레기로 처리해야 합니다.',
        31: '일회용 수저는 일반쓰레기로 분리 배출해야 하며, 이는 재활용 가능성이 낮기 때문입니다.',
        32: '기름종이는 오염된 상태에서의 재활용이 불가능하므로 일반쓰레기로 처리해야 합니다.',
        33: '포장용 비닐은 비닐류로 분리 배출해야 하며, 이는 재활용 가능성을 높이기 위한 조치입니다.',
        34: '종이 가방은 종이류로 분리배출할 수 있습니다.',
        35: '페트병의 라벨은 비닐류로 처리해야 하며, 이는 재활용 과정에서의 혼합 오염을 방지하기 위한 조치입니다.',
        36: '식용유 통은 비워서 플라스틱류로 처리해야 합니다.',
        37: '미사용 세제 용기는 플라스틱류로 배출해야 합니다.',
        38: '우편봉투는 종이류로 분리배출할 수 있습니다.',
        39: '종이 타올 심지는 오염된 상태에서의 재활용이 불가능하여 일반쓰레기로 처리해야 합니다.',
        40: '리사이클이 가능한 플라스틱 컵은 플라스틱류로 배출해야 합니다.',
        42: '식품 포장용 폼은 재활용이 되지 않아 일반쓰레기로 처리해야 합니다.',
        43: '음식물이 남아있다면 플라스틱류가 아닌 일반쓰레기로 배출해야 합니다.',
        46: '재활용이 불가능한 스티로폼은 재활용 공정에서의 처리 가능성이 낮기 때문에 일반쓰레기로 처리해야 합니다.',
        48: '주방 타올은 사용 후 일반쓰레기로 처리해야 합니다.',
        49: '냉동식품 포장지는 일반쓰레기로 배출해야 합니다.',
        50: '일회용 커피컵의 뚜껑은 플라스틱류로 분리배출해야 합니다.'
    }

    # 사용자 입력 답변을 숫자로 변환
    try:
        user_answer = int(user_answer)  # 사용자의 답변을 숫자로 변환
    except ValueError:
        return jsonify({'message': 'Answer must be a number'}), 400

    # 정답 및 풀이 설정
    solution_text = solution.get(question_num, "No solution available")
    if question_num in correct_answers and user_answer in correct_answers[question_num]:
        result = 'Right'
    else:
        result = 'Wrong'

    # 정답에 맞는 점수 계산
    q_score = 20 if result == 'Right' else 0

    # 가장 최근 `login_count` 증가 사용자 찾기
    user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()
    if not user_log:
        return jsonify({'message': 'No user log found'}), 404

    user_nickname = PhoneNumber.query.filter_by(phone_number=user_log.phone_number).first().nickname

    # 기존 CompareResult 값 가져오기
    existing_result = CompareResult.query.filter_by(nickname=user_nickname).first()

    if existing_result:
        # 기존 점수와 새로운 점수를 합산
        existing_result.score += q_score
        existing_result.result = result
    else:
        # 새로운 CompareResult 추가
        compare_result = CompareResult(
        result=result,
        score= q_score,
        nickname=user_nickname
        )
        db.session.add(compare_result)

    # 변경 사항 커밋
    db.session.commit()

    return jsonify({
        'result': result,
        'score': q_score,
        'solution': solution_text
    }), 200


@app.route('/send_result', methods=['GET'])
def send_result():
    # 'result' 파라미터를 쿼리 스트링에서 받기
    result = request.args.get('result')  # 예: /send_result?result=right

    # result 값에 따라 점수 설정
    if result == 'right':
        score += 20
    else:
        score += 0

    # 점수 반환
    return jsonify({'score': score})



@app.route('/get-trash-counts', methods=['GET'])
def get_trash_counts():
    try:
        # 최근 로그인 카운트 증가한 사용자 찾기
        recent_user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()

        if not recent_user_log:
            return jsonify({'message': 'No user log found'}), 404
        
        # 해당 사용자의 닉네임 가져오기
        user_nickname = PhoneNumber.query.filter_by(phone_number=recent_user_log.phone_number).first().nickname

        # 해당 닉네임의 TrashCount 찾기
        trash_count = TrashCount.query.filter_by(nickname=user_nickname).first()

        if not trash_count:
            return jsonify({'message': 'No trash counts found for this nickname'}), 404
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred while fetching trash counts"}), 500

    # 카운트 정보 반환
    return jsonify({
        'plastic_count': trash_count.plastic_count,
        'vinyl_count': trash_count.vinyl_count,
        'can_count': trash_count.can_count,
        'general_count': trash_count.general_count
    }), 200


@app.route('/get-latest-score', methods=['GET'])
def get_latest_score():
    try:
        # 최근 로그인 카운트 증가한 사용자 찾기
        recent_user_log = UserLog.query.order_by(UserLog.login_time.desc()).first()

        if not recent_user_log:
            return jsonify({'message': 'No user log found'}), 404

        # 해당 사용자의 닉네임 가져오기
        user_nickname = PhoneNumber.query.filter_by(phone_number=recent_user_log.phone_number).first().nickname

        # 닉네임으로 최근 비교 결과 가져오기
        recent_compare_result = CompareResult.query.filter_by(nickname=user_nickname).order_by(CompareResult.id.desc()).first()

        if not recent_compare_result:
            return jsonify({'message': 'No compare result found for this nickname'}), 404

        # 결과 반환
        return jsonify({
            'nickname': recent_compare_result.nickname,
            'result': recent_compare_result.result,
            'score': recent_compare_result.score  # 누적된 점수 반환
        }), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred while fetching the latest score"}), 500


# 점수 순위 조회
@app.route('/rankings', methods=['GET'])
def get_rankings():
    # CompareResult에서 모든 결과를 가져와서 점수에 따라 정렬
    results = CompareResult.query.order_by(CompareResult.score.desc()).all()

    # 결과를 순위 형식으로 변환
    rankings = []
    for rank, result in enumerate(results, start=1):
        rankings.append({
            'rank': rank,
            'nickname': result.nickname,
            'score': result.score
        })
    return jsonify(rankings), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)