RESTful API
===========

Обработка ошибок
----------------

В случае ошибки возвращается HTTP-статус с кодом ошибки.
Детали ошибки в поле detail ответа.


Управление IP
-------------

# Запрос и обновление

    PATCH /ip/:id/  key=value
    GET /ip/:id/
    
# Поиск IP

    GET /ip/[?key=value&...]
        key - имя поля. key поддерживает все lookup из Django Query API.
        value - значение
        
    /ip/?address=46.17.40.11
    /ip/?address__contains=17.40
    /ip/?address__contains=17.40&status=free

# Получить count свободных IP из списка пулов 

    GET /ip/rent/pool?pool=a[&pool=b&...&count=1]

# Получить count свободных IP из свободных пулов в ЦОД

    /ip/rent/dc?dc=N[&v=4&count=1]
