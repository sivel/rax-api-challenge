# rax-api-challenge

## Rules:
- In order to submit your answers for prizes, you must:
  - Create a public github account and push your answers to a new repository with filenames of challenge1, challenge2, etc.
  - Submit your repository using the form [here]() by April 10th.
- Languages allowed:
   - You are encouraged to use one of the following Software Development Kits (SDK):
     - [Pyrax for Python](http://docs.rackspace.com/sdks/guide/content/python.html)
     - [jClouds for Java](http://docs.rackspace.com/sdks/guide/content/java.html)
     - [PHP-Opencloud for PHP](http://docs.rackspace.com/sdks/guide/content/php.html)
   - Other Languages which do not have an official Rackspace SDK yet:
     - Ruby ([fog](http://fog.io/))
     - Node.js ([pkgcloud](https://github.com/nodejitsu/pkgcloud))
   - Languages that you are strongly encouraged to avoid:
     - Bash / Shell
- For all challenges, you can assume that a valid credentials file with the username and API key exist at ~/.rackspace_cloud_credentials
- Nothing will be graded or judged until the contest is over on April 10th. At that time, your repository will be cloned and reviewed.

## What was that about Prizes?
Over the next few weeks, there will be the opportunity to earn a total of 30 points from the different challenges being sent out.

- If you earn at least 5 Points: You get a super cool, limited edition, first run "API Savvy" button for your lanyard.
- If you earn at least 12 Points: You get a $5 gift certificate for Ground Town
- If you earn at least 25 Points: You get a Raspberry Pi (http://www.raspberrypi.org/faqs)

In addition to using this as an opportunity to grow knowledge around Rackspace, we will also be selecting the best submissions and adding them to a customer facing Code Snippets page. This will be a place customers can go to get example code that solves real life problems.

## Questions:
### I'm far from an expert developer. Should I even try this?
Yes! The goal is to get out of your comfort zone and expand your skill set. All of the Rackspace SDKs listed above have a great "Samples" section with code that you can use as a jumping off point. We have created a new internal forum category [here]() where you can ask for help and discuss each challenge. [Codecademy.com](http://www.codeacademy.com/) is also a great resource for building a development foundation.

### I've never used github, and you scared me with all this talk about repositories, pushing, and cloning.
It's not as scary as it sounds. Check out [try.github.com](http://try.github.com/) for a quick crash course, and if you can't figure it out, jump into the internal forums above and ask for a hand.

### Why can't I use bash?!
The goal of this project is to identify Rackers who have a passion to learn DevOps and grow our knowledge so we can support our customers using the API. The fact is, the majority of our customers using the API do so with advanced languages like Python and Ruby, and not by using curl in bash scripts. 

## Ok, this sounds like fun, bring on the challenges!

### Challenge 1

Write a script that builds three 512 MB Cloud Servers that follow a similar naming convention. (ie., web1, web2, web3) and returns the IP and login credentials for each server. Use any image you want. ***Worth 1 point***

### Challenge 2

Write a script that clones a server (takes an image and deploys the image as a new server). ***Worth 1 Point***

### Challenge 3

Write a script that accepts a directory as an argument as well as a container name. The script should upload the contents of the specified directory to the container (or create it if it doesn't exist). The script should handle errors appropriately. (Check for invalid paths, etc.) ***Worth 3 Points***

### Challenge 4

Write a script that uses Cloud DNS to create a new A record when passed a FQDN and IP address as arguments. ***Worth 1 Point***

### Challenge 5

Write a script that creates a Cloud Database instance. This instance should contain at least one database, and the database should have at least one user that can connect to it. ***Worth 1 Point***

### Challenge 6

Write a script that creates a CDN-enabled container in Cloud Files. ***Worth 1 Point***

### Challenge 7

Write a script that will create 2 Cloud Servers and add them as nodes to a new Cloud Load Balancer. ***Worth 3 Points***

###Challenge 8

Write a script that will create a static webpage served out of Cloud Files. The script must create a new container, cdn enable it, enable it to serve an index file, create an index file object, upload the object to the container, and create a CNAME record pointing to the CDN URL of the container. ***Worth 3 Points***