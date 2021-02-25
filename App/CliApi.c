#include <stdio.h>
#include <sys/socket.h> 
#include <TrafficGenerator.c>
#include <Capturer.c>

int main(int argc , char *argv[])
{
	// printf(" ");
	generateTraffic();
}

int createSocket()
{
	int socket_desc;
	socket_desc = socket(AF_INET , SOCK_STREAM , 0);
	
	if (socket_desc == -1)
	{
		printf("Could not create socket\n");
	}
	else 
    {
        printf("socket created successfully\n");
    }
	return socket_desc;
}