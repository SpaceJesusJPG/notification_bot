import paramiko


class SshHandler:
    def __init__(self, host):
        self.hostname, self.user, self.secret, self.verbose_name = host
        self.client = paramiko.SSHClient()

    def connect(self):
        try:
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                username=self.user,
                password=self.secret,
                timeout=5,
            )
            return (True,)
        except Exception as err:
            return False, err

    def close(self):
        self.client.close()

    def get_status(self):
        status = self.client.exec_command(
            "systemctl show --no-page geo | grep -e ActiveState -e CPUUsageNSec"
        )[1].read()
        last_data = self.client.exec_command(
            "cd dev/com_reader/data; find . -cmin -10 -exec tail -n 1 {} \; | sort"
        )[1].read()
        status_decoded = {
            i.decode().split("=")[0]: i.decode().split("=")[1]
            for i in status.split(b"\n")[:-1]
        }
        return status_decoded, last_data.decode().strip()
