# Обновление

## Скрипт обновления ОС CentOS

```bash
ssh-keygen -R IPorHOSTNAME
ssh-keyscan -H IPorHOSTNAME >> ~/.ssh/known_hosts
sshpass -p PASSWORD ssh -l root IPorHOSTNAME 'bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh) && reboot'
```

```bash
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/setup.sh)
```

## Скрипт обновления ОС Debian/Ubuntu

```bash
wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/debian/default.sh
bash default.sh
```

# Установка

## Скрипт установки DirectAdmin

```bash
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/directadmin/setup.sh)
```

## Скрипт установки Vesta

### Debian/Ubuntu

```bash
wget --no-check-certificate https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh
bash setup.sh
```

### CentOS
```bash
bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/vesta/setup.sh)
```

# Особенности

При установке ОС CentOS/Debian/Ubuntu на физический сервер или VPS KVM, ставится APF и BFD
