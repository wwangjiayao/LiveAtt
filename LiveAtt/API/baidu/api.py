from aip import AipFace
import base64
import json
def search_baidu(image_path):
    
    response = {}

    APP_ID = "6824119"
    API_KEY = "ByxUCiePRcASHdERl76ynkPx"
    SECRET_KEY = 'PSN7EHur485OsxtJ2rQ4yPz94vfC0t2u'
    client = AipFace(APP_ID, API_KEY, SECRET_KEY)
    
    # 读取图片内容并进行Base64编码
    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')  

    imageType = "BASE64"
    groupIdList = "class1"
    result = client.search(image_data, imageType, groupIdList);
    print(result)

    if result['error_msg'] == 'SUCCESS':
        
        user_id = result['result']['user_list'][0]['user_id']
        score = result['result']['user_list'][0]['score']
        response['user_id']=result['result']['user_list'][0]['user_info']
        print(f"SUCCESS! \nuser_id:{user_id}")
    
        response['score'] = score
        
        # 活体+ 表情 + 年龄 + 性别 检测 
        options = {}
        options["face_field"] = "age,expression,gender"
        options["max_face_num"] = 2
        options["liveness_control"] = "LOW"
        res = client.detect(image_data, imageType, options)
        
        if res['error_msg'] == 'SUCCESS':
            
            base = res['result']['face_list'][0]
            live = base['liveness']['livemapscore']
            age = base['age']
            expression = base['expression']['type']
            gender = base['gender']['type']
            
            response['live'] = live
            response['age'] = age
            response['expression'] = expression
            response['gender'] = gender
            
            print(f"age:{age} expression:{expression} gender:{gender}")
            
            if (float(live) < 0.6):
                print(f"The liveness test failed! live:{live} < 0.6")
                live_pass = "UNPASS"
                response['livepass'] = live_pass
            else:
                print(f"The liveness test passed! live:{live} > 0.6 ")
                live_pass = "PASS"
                response['livepass'] = live_pass
        
    else:
        user_id = -1
        response['user_id']="None"
        print(f"ERROR! user_id:{user_id}")
    
    return response

