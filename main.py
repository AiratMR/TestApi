import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from websocket import ConnectionManager

from models import AlarmClock

app = FastAPI(title="Alarm clocks api")
manager = ConnectionManager()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>Alarm chat</h1>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    """
    Стартовая страница с демонстрацией работы веб-сокета
    """
    return HTMLResponse(html)


@app.get("/alarmclocks")
async def get_alarm_clocks():
    """
    Получение списка всех еще не прозвеневших будильников
    """
    result = []
    query = AlarmClock.select().where(AlarmClock.alarm_time >= datetime.now())
    for clock in query:
        result.append({"alarm_time": clock.alarm_time, "description": clock.description})
    return result


@app.post("/alarmclocks", status_code=201)
async def create_alarm_clock(request):
    """
    Добавление будильника в базу
    :param request: dict
        {
            "alarm_time": "date/month/year hour:minute:second",
            "description": "some text"
        }
    """
    request_dict = json.loads(request)
    date_time = datetime.strptime(request_dict["alarm_time"], '%d/%m/%y %H:%M:%S')
    description = request_dict["description"]
    AlarmClock.create(alarm_time=date_time, description=description)
    return request_dict


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Веб-сокет, оповещающий о прозвеневшем будильнике
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await alarm_check_task()
            if data is not None:
                await manager.broadcast(f"Alarm: {data.description}")
                query = AlarmClock.delete().where(AlarmClock.alarm_time < datetime.now())
                query.execute()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def alarm_check_task():
    """
    Проверка прозвеневших будльников
    """
    alarm_clock = AlarmClock.select().order_by(AlarmClock.alarm_time)
    await asyncio.sleep(10)

    for clock in alarm_clock:
        time_now = datetime.now()
        alarm_time = clock.alarm_time
        if time_now.date() == alarm_time.date():
            if time_now.hour == alarm_time.hour and time_now.minute == alarm_time.minute:
                return clock
    return None
