        // 只是包含纯js代码
        //将签到结果容器 id="results" 改回 id="dynamicTitle"
        // JS document.getElementById('dynamicTitle') 保持一致。这样交互时返回内容才能正确显示。
        document.addEventListener('DOMContentLoaded', function() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const context = canvas.getContext('2d');
            const snaps = [
                document.getElementById('snap1'),
                document.getElementById('snap2'),
                document.getElementById('snap3'),
                document.getElementById('snap4')
            ];
            const startCamera = document.getElementById('startCamera');
            const stopCamera = document.getElementById('stopCamera');
            const resultsDiv = document.getElementById('dynamicTitle');
            resultsDiv.style.display = 'none';
            let streamReference = null;

            function startCameraFunction() {
                if (navigator.mediaDevices?.getUserMedia) {
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(function(stream) {
                            streamReference = stream;
                            video.srcObject = stream;
                            video.play().catch(e => console.error("Video play error:", e));

                            // Show elements
                            video.style.display = 'block';
                            snaps.forEach(snap => snap.style.display = 'inline');
                            stopCamera.style.display = 'inline';
                            startCamera.style.display = 'none';
                        })
                        .catch(function(err) {
                            console.error("Camera error:", err);
                            alert("无法访问摄像头，请检查权限。");
                        });
                } else {
                    alert("您的浏览器不支持摄像头访问。");
                }
            }

            function stopCameraFunction() {
                if (streamReference) {
                    resultsDiv.textContent = '';
                    resultsDiv.style.display = 'none';
                    streamReference.getTracks().forEach(track => track.stop());
                    video.style.display = 'none';
                    snaps.forEach(snap => snap.style.display = 'none');
                    stopCamera.style.display = 'none';
                    startCamera.style.display = 'inline';
                    streamReference = null;
                }
            }

            startCamera.addEventListener('click', startCameraFunction);
            stopCamera.addEventListener('click', stopCameraFunction);

            // 1) 按钮1：独立处理——调用/API_1
            snaps[0].addEventListener('click', () => {
              if (!streamReference) return;
              captureAndFetch(1, '/API_1', renderAttendanceResult);
            });

            // 2) 按钮2：独立处理——调用/API_2并显示两张人脸
            snaps[1].addEventListener('click', () => {
              if (!streamReference) return;
              captureAndFetch(2, '/API_2', renderMatchResult);
            });

            // 2) 按钮4：独立处理——调用/API_4并显示两张人脸
            snaps[3].addEventListener('click', () => {
              if (!streamReference) return;
              captureAndFetch(4, '/API_4', renderMatchResult);
            });

            /**
             * captureAndFetch
             *   index：按钮索引（仅用于文件名唯一性）
             *   apiUrl：'/API_1'或'/API_2'
             *   renderer：回调函数(data) → 构建innerHTML
             */
            function captureAndFetch(index, apiUrl, renderer) {
              // 1. 截取图像快照
              canvas.width  = video.videoWidth;
              canvas.height = video.videoHeight;
              context.drawImage(video, 0, 0, canvas.width, canvas.height);
              const dataUrl = canvas.toDataURL('image/jpeg', 0.8);

              // 2. 显示加载 spinner
              resultsDiv.innerHTML = `
                <div class="processing">
                  <i class="fas fa-spinner fa-spin"></i>
                  <span>正在处理中，请稍候...</span>
                </div>
              `;
              resultsDiv.style.display = 'block';

              // 3. 发送请求
              fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataUrl })
              })
              .then(r => r.ok ? r.json() : Promise.reject('网络错误'))
              .then(renderer)
              .catch(err => {
                console.error(`${apiUrl} 错误:`, err);
                resultsDiv.innerHTML = `
                  <div class="result-error">
                    <div class="result-icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <div class="result-content">
                      <h3>处理请求时出错</h3>
                      <p>请重试或联系管理员</p>
                    </div>
                  </div>
                `;
              });
            }

            /**
             * renderAttendanceResult(data)
             *   用于 POST /API_1 返回的考勤结果渲染
             *   data 可能包含：
             *     - pass:       "PASS" 或 undefined
             *     - livepass:   "PASS" 或 undefined
             *     - user_id:    姓名
             *     - score:      相似度（保留两位小数）
             *     - gender:     'Male' | 'Female'
             *     - age:        数字
             *     - expression: 表情描述
             */
            function renderAttendanceResult(data) {
              let html = '';

              // 1) 注册并通过
              if (data.pass === "PASS") {
                html = `
                  <div class="result-success">
                    <div class="result-icon">
                      <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="result-content">
                      <h3>${data.user_id}，欢迎您！</h3>
                      <p>您已成功完成签到！</p>
                    </div>
                  </div>
                  <div class="result-details">
                    <div class="detail-item">
                      <span class="detail-label">相似度:</span>
                      <span class="detail-value">${data.score}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">性别:</span>
                      <span class="detail-value">${data.gender === 'Male' ? '男' : '女'}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">年龄:</span>
                      <span class="detail-value">${data.age}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">表情:</span>
                      <span class="detail-value">${data.expression}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">活体检测:</span>
                      <span class="detail-value ${data.livepass === 'PASS' ? 'text-success' : 'text-danger'}">
                        ${data.livepass === 'PASS' ? '通过' : '未通过'}
                      </span>
                    </div>
                  </div>
                `;

              // 2) 未注册但活体通过
              } else if (data.livepass === "PASS") {
                html = `
                  <div class="result-fail">
                    <div class="result-icon">
                      <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <div class="result-content">
                      <h3>签到失败</h3>
                      <p>抱歉... 您未在系统中注册！</p>
                    </div>
                  </div>
                `;

              // 3) 注册了但活体未通过（或者两者都未通过）
              } else {
                html = `
                  <div class="result-fail">
                    <div class="result-icon">
                      <i class="fas fa-times-circle"></i>
                    </div>
                    <div class="result-content">
                      <h3>签到失败</h3>
                      <p>抱歉 ${data.user_id}... 您未通过活体检测！</p>
                    </div>
                  </div>
                  <div class="result-details">
                    <div class="detail-item">
                      <span class="detail-label">活体检测:</span>
                      <span class="detail-value text-danger">未通过</span>
                    </div>
                  </div>
                `;
              }

              // 渲染并显示
              resultsDiv.innerHTML = html;
              resultsDiv.style.display = 'block';
            }

            /**
             * renderMatchResult(data)
             *   用于API_2
             */
            function renderMatchResult(data) {
              // 情况 1：活体检测失败（非真人）
              if (data.status === 'fail' && data.reason === '活体检测未通过') {
                resultsDiv.innerHTML = `
                  <div class="result-error">
                    <div class="result-icon"><i class="fas fa-user-secret"></i></div>
                    <div class="result-content">
                      <h3>❌活体检测未通过</h3>
                      <br>
                      <p>评分: <strong>${data.liveness_score?.toFixed(2) ?? 'N/A'}</strong></p>
                      <br>
                      <p>系统判断为假体，请重试并使用真人拍摄。</p>
                    </div>
                  </div>
                `;
                return;
              }

              // 情况 2：活体检测通过，但人脸匹配失败
              if (data.liveness_pass === true && data.pass === 'UNPASS') {
                  resultsDiv.innerHTML = `
                    <div class="match-info text-center">
                      <div class="detail-item">
                        <strong>🎉 活体检测成功</strong><br>
                        <p>活体评分: <strong>${data.liveness_score?.toFixed(2) ?? 'N/A'}</strong></p>
                        <br>
                        <br>
                      </div>
                    </div>

                    <div class="match-container">
                      <div class="face-block">
                        <h4>识别人脸</h4>
                        <img src="${data.target_face}" alt="上传人脸">
                      </div>
                    </div>

                    <div class="match-info text-center">
                      <div class="detail-item"><strong>相似度：</strong>${data.score}</div>
                      <div class="detail-item text-danger"><strong>人脸匹配失败，未找到相似人脸，请摆正姿态并正视摄像头</strong></div>
                    </div>
                  `;
                  return;
              }


              // 情况 3：活体检测通过，匹配成功
              if (data.liveness_pass === true && data.pass === 'PASS') {
                  resultsDiv.innerHTML = `
                    <div class="match-info text-center">
                      <div class="detail-item">
                        <strong>🎉 活体检测成功</strong><br>
                        <p>活体评分: <strong>${data.liveness_score?.toFixed(2) ?? 'N/A'}</strong></p>
                        <br>
                        <br>
                      </div>
                    </div>

                    <div class="match-container">
                      <div class="face-block">
                        <h4>识别人脸</h4>
                        <img src="${data.target_face}" alt="上传人脸">
                      </div>
                      <div class="face-block">
                        <h4>系统匹配</h4>
                        <img src="${data.match_face}" alt="匹配人脸">
                      </div>
                    </div>

                    <div class="match-info text-center">
                      <div class="detail-item"><strong>学号：</strong>${data.student_id}</div>
                      <div class="detail-item"><strong>姓名：</strong>${data.user_id}</div>
                      <div class="detail-item"><strong>相似度：</strong>${data.score}</div>
                      <div class="detail-item">
                        <strong>状态：</strong>
                        <span class="text-success">通过</span>
                      </div>
                    </div>
                  `;
                  return;
              }

            }

            // 第三按钮：活体检测视频录制与美化进度条
            snaps[2].addEventListener('click', async () => {
                if (!streamReference) return;
                const actionsQueue = ['blink', 'mouth', 'head'];
                const actionNames = { blink: '眨眼检测', mouth: '张嘴检测', head: '转头检测' };
                let currentAction = 0;

                resultsDiv.innerHTML = '';
                resultsDiv.style.display = 'block';

                // 创建提示和进度容器
                const container = document.createElement('div');
                container.classList.add('liveness-container');
                const actionLabel = document.createElement('h4');
                actionLabel.classList.add('action-label');
                container.appendChild(actionLabel);

                const progressWrapper = document.createElement('div');
                progressWrapper.classList.add('progress-wrapper');
                const progressBar = document.createElement('div');
                progressBar.classList.add('progress-bar');
                progressWrapper.appendChild(progressBar);
                container.appendChild(progressWrapper);

                resultsDiv.appendChild(container);

                await fetch('/API_Reset', { method: 'POST', headers: { 'Content-Type': 'application/json' } });

                const recordVideo = durationMs => new Promise((resolve) => {
                    const chunks = [];
                    const recorder = new MediaRecorder(video.srcObject, { mimeType: 'video/webm' });
                    recorder.ondataavailable = e => e.data.size && chunks.push(e.data);
                    recorder.onstop = () => {
                        const blob = new Blob(chunks, { type: 'video/webm' });
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    };
                    recorder.start();
                    setTimeout(() => recorder.stop(), durationMs);
                });

                while (currentAction < actionsQueue.length) {
                    const key = actionsQueue[currentAction];
                    const name = actionNames[key];
                    actionLabel.textContent = `现执行：${name}`;
                    progressBar.style.width = '0%';

                    // animate progress
                    const total = 3000, step = 50;
                    let percent = 0;
                    const timer = setInterval(() => {
                        percent += (step / total) * 100;
                        progressBar.style.width = `${percent}%`;
                        if (percent >= 100) clearInterval(timer);
                    }, step);

                    const videoData = await recordVideo(total);
                    const resp = await fetch('/API_3', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ video: videoData })
                    });
                    const data = await resp.json();

                    if (!data.pass) {
                        actionLabel.textContent = '活体检测未通过，流程终止';
                        break;
                      }

                      if (data.is_final) {
                        if (data.face_match) {
                          actionLabel.textContent = '欢迎 ' + data.matched_name + ' 同学，您已完成签到';
                        } else {
                          actionLabel.textContent = '人脸匹配失败，签到失败';
                        }
                        progressBar.style.width = '100%';
                        break;
                      }

                    currentAction++;
                }
            });

            // 添加样式到页面
            const style = document.createElement('style');
            style.textContent = `
                #dynamicTitle {
                    background: white;
                    border-radius: 8px;
                    padding: 1.5rem;
                    margin-top: 1rem;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    width: 100%;
                    max-width: 500px;
                }

                .processing {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.75rem;
                    color: var(--primary);
                }

                .liveness-container { padding: 16px; background: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
                .action-label { margin-bottom: 8px; font-size: 1.1rem; color: #333; }
                .progress-wrapper { width: 100%; background: #e0e0e0; border-radius: 12px; overflow: hidden; height: 12px; margin-bottom: 12px; }
                .progress-bar { width: 0; height: 100%; background: linear-gradient(90deg, #4facfe, #00f2fe); transition: width 0.1s ease; }
                .error { color: #d9534f; }
                .processing { display: flex; align-items: center; gap: 8px; }

                .processing i {
                    font-size: 1.5rem;
                }

                .result-success, .result-fail, .result-error {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }

                .result-icon i {
                    font-size: 2.5rem;
                }

                .result-success .result-icon i {
                    color: #10B981;
                }

                .result-fail .result-icon i {
                    color: #EF4444;
                }

                .result-error .result-icon i {
                    color: #F59E0B;
                }

                .result-content h3 {
                    margin: 0 0 0.25rem 0;
                    font-size: 1.25rem;
                }

                .result-content p {
                    margin: 0;
                    color: #6B7280;
                }

                .result-details {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 0.75rem;
                    border-top: 1px solid #E5E7EB;
                    padding-top: 1rem;
                }

                .detail-item {
                    display: flex;
                    justify-content: space-between;
                }

                .detail-label {
                    color: #6B7280;
                }

                .detail-value {
                    font-weight: 500;
                }

                .text-success {
                    color: #10B981;
                }

                .text-danger {
                    color: #EF4444;
                }

                .match-container {
                  display: flex;
                  flex-wrap: wrap;
                  gap: 20px;
                  justify-content: center;
                  margin-bottom: 15px;
                }

                .face-block {
                  flex: 1;
                  min-width: 200px;
                  text-align: center;
                }

                .face-block img {
                  max-width: 100%;
                  border-radius: 10px;
                  box-shadow: 0 0 6px rgba(0, 0, 0, 0.2);
                }

                .match-info .detail-item {
                  font-size: 16px;
                  margin: 5px 0;
                  text-align: center;
                }


            `;
            document.head.appendChild(style);
        });