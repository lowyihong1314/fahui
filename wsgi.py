from app import create_app

app = create_app(env="prod")

# tail -f /home/utba/flaskapp/fahui/fahui.out.log
# tail -f /home/utba/flaskapp/fahui/fahui.err.log
# # 启动
# sudo systemctl start fahui

# # 停止
# sudo systemctl stop fahui

# # 重启
# sudo systemctl restart fahui

# # 状态
# sudo systemctl status fahui

# # 看日志
# journalctl -u fahui -n 100
