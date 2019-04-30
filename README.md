# midcli
NAS Command Line Interface

Software in ALPHA state, highly experimental.\
No bugs/features being accepted at the moment.


### Examples

Listing available commands in the current namespace.

```
root@freenas[~]# cli

> list
..
account
system
directoryservice
service
sharing
task
storage
network
jail
pool
vm
>
```


Creating a system tunable of variable "FOO", value "BAR" and of "RC" type.

```
root@freenas[~]# cli

> system
system> tunable
system tunable> create var=FOO value=BAR type=RC
system tunable>
```

Enabling root SSH and starting the service.

```
root@freenas[~]# cli

> service ssh update rootlogin=true
> service update id_or_name=ssh enable=true
> service start service=ssh
```
