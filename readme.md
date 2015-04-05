Install ansible and deps

```
sudo apt-get install python-pip facter
sudo pip install ansible

```

Add localhost entry to `/etc/ansible/hosts`

```
localhost ansible_connection=local
```

Enable source repositories in sources.list somehow

Add the following to `sudo nano /etc/ansible/facts.d/main.fact` (this is hard to query reliably from mint)

```
[ubuntu]
release=trusty
```