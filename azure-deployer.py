import subprocess as sb
import argparse
import os

NODECOUNT = 2
SKU = 'Basic'
NODE_VM_SIZE = 'Standard_DS2_v2'
LOCATION = 'eastus'
RESOURCE_GROUP_FLAG=0

def create_resourceGroup(resourceGroup):
    try:
        sb.run('az group create --name '+resourceGroup+' --location '+LOCATION, shell=True)
        print("Resource Group Created Successfully")
        RESOURCE_GROUP_FLAG=1
    except e:
        print("Error {}".format(e))
    return None

def delete_resourceGroup(resourceGroup):
    try:
        sb.run('az group delete --name '+resourceGroup+ ' --yes',shell=True)
    except e:
        print("Resource Group Deletion Failed! Please delete it manually")
        print("Error {}".format(e))
        

def create_registry(resourceGroup, registryName):
    try:
        command = 'az acr create --resource-group ' +resourceGroup+' --name '+registryName+' --sku '+SKU
        sb.run(command,shell = True)
        print("Container Created Succesfully")
    except e:
        print("Error {}".format(e))

    return None

def registryLogin(registryName):
    try:
        sb.run('az acr login --name '+registryName,shell= True)
    except e:
        print("Error {}".format(e))
    return None

def pushRegistryImage(registryName, images):
    for image in images:
        image_tag = image.split('/')[-1]
        acr_image = image_tag.split(':')[0]
        tag = image_tag.split(':')[-1]
        namespace = 'packages_tiger/' + tag +'/'
        try:
            print('1st Step Completed')
            sb.run('docker tag ' + image+':'+tag+ ' ' + registryName+'.azurecr.io' +'/'+namespace+acr_image+':'+tag, shell=True)
            sb.run('docker push ' + registryName+'.azurecr.io' +'/'+namespace+acr_image+':'+tag, shell=True)

        except e:
            print("Image upload failed. Uploaded till above this"+ str(image))
            print("Error {}".format(e))
            os._exit(0)
    return  None

def createCluster(resourceGroup, registryName, clusterName):
    try:
        sb.run('az aks create --resource-group '+resourceGroup+  ' --name '+ clusterName + ' --node-count '+ str(NODECOUNT) + ' --enable-managed-identity  --network-plugin azure --network-policy azure --attach-acr ' + registryName+' --node-vm-size '+NODE_VM_SIZE , shell =True)
        print("Cluster created successfully")
        sb.run('az aks get-credentials --resource-group '+resourceGroup+' --name '+ clusterName, shell = True)
        print("Cluster Credentials added")
    except e:
        if(RESOURCE_GROUP_FLAG==1):
            delete_resourceGroup(resourceGroup)
        print("Error {}".format(e))
        os._exit(0)

def createClusterwithoutRegistry(resourceGroup,clusterName):
    try:
        sb.run('az aks create --resource-group '+resourceGroup+  ' --name '+ clusterName + ' --node-count '+ str(NODECOUNT) + ' --enable-managed-identity  --network-plugin azure --network-policy azure --node-vm-size '+NODE_VM_SIZE , shell =True)
        print("Cluster created successfully")
        sb.run('az aks get-credentials --resource-group '+resourceGroup+' --name '+ clusterName, shell = True)
        print("Cluster Credentials added")
    except e:
        if(RESOURCE_GROUP_FLAG==1):
            delete_resourceGroup(resourceGroup)
        print("Error {}".format(e))
        os._exit(0)


def deleteCluster(resourceGroup, clusterName):
    try:
        sb.run('az aks delete --name '+clusterName+ '  --resource-group '+resourceGroup+' -y',shell= True)
        print("Cluster Deleted Succesfully")
    except e:
        print("Error {}".format(e))
        print("Deletion of cluster failed")
        os._exit(0)
    return None
def deleteRegistry(resourceGroup, registryName):
    try:
        sb.run('az acr delete --name '+registryName+ '  --resource-group '+resourceGroup+' --yes',shell= True)
        print("Registry Deleted Succesfully")
    except e:
        print("Error {}".format(e))
        print("Deletion of Container registry failed")
        os._exit(0)
    return None



if __name__== "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create',action='store_true')
    group.add_argument('--delete',action='store_true')
    registryOption = parser.add_mutually_exclusive_group()
    registryOption.add_argument("--createRegistry",action='store_true')
    registryOption.add_argument("--attachRegistry",action='store_true')
    
    parser.add_argument("-rg","--resourceGroup", help = "Enter the name of the resource Group",required=True)
    parser.add_argument("-cn","--clusterName", help = "Name of the cluster", required=True)
    parser.add_argument("-r","--registryName", help = "Enter the name of the registry")
    parser.add_argument("-i","--images",nargs='+',help ="Enter the list of the image")
    parser.add_argument("-n", "--nodeCount", help = "Enter the number of nodes")
    parser.add_argument("-sku","--sku",help = "AzureContainerRegistryPlan! Default is Basic")
    parser.add_argument("--vmSize",help="Default is Standard_DS2_V2")
    parser.add_argument("--location", help="Default location is US-EAST")
    args = parser.parse_args()

    resourceGroup = args.resourceGroup
    registryName = args.registryName
    clusterName = args.clusterName
    

    if(args.delete):
        delete_resourceGroup(resourceGroup)
        os._exit(0)

    if (args.nodeCount):
        NODECOUNT = args.nodeCount
    if(args.sku):
        SKU=args.sku
    if(args.vmSize):
        NODE_VM_SIZE=args.vmSize

    if (args.createRegistry):
        if (args.images== None):
            print("Image name not provided")
            os._exit(0)
        if(args.registryName == None):
            print("Provide a registry name")
            os._exit(0)
        create_resourceGroup(resourceGroup)
        create_registry(args.resourceGroup,registryName)
        registryLogin(registryName)
        pushRegistryImage(registryName,args.images)
        createCluster(resourceGroup,registryName,clusterName)
    
    if(args.attachRegistry):
        if(args.registryName == None):
            print("Provide a registry name")
            os._exit(0)
        create_resourceGroup(resourceGroup)
        createCluster(resourceGroup,registryName,clusterName)

    if(args.create and args.createRegistry==None and args.attachRegistry==None):
        createClusterwithoutRegistry(resourceGroup,clusterName)


