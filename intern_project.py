import requests
import json
import base64
import os

images_dict = {}

def pretty(obj):
	return json.dumps(obj, sort_keys = True, indent = 2)

facerec_folder = '/Users/jloc0002/Desktop/python/facerec'
testimgs_folder = '/Users/jloc0002/Desktop/python/testimgs'

def get_images(rootdir):
	image_list = []
	for subdir, dirs, files in os.walk(rootdir):
		for file in files:
			image_path = os.path.join(subdir, file)
			image_list.append(image_path)
	return image_list

#encode images:

def encode_image(image):
	with open(image, 'rb') as f:
		q = f.read()
		s = q.encode('base64')
	return s

#retrieves Clarifai access_token:

apid = {'client_id':'qBQDWmYOFcSAipwhEIT7joZ-FXOKkkPVrq-exAfe', 'client_secret':'C8_UWzh0ErmQhnUc5-k4ePbgQOocxI_qH3g-d3XJ', 'grant_type':'client_credentials'}
apiresult = requests.post("https://api.clarifai.com/v1/token/", params=apid)
x = json.loads(apiresult.text)
access_token = x['access_token']

#tags photos using Clarifai. Creates dictionary for each image.:

def create_dict():
	for image in get_images(testimgs_folder)[1:]:
		photo_tags = []
		h = {'Authorization':'Bearer %s' %access_token}
		encodedImage = encode_image(image)
		d = {'encoded_data':encodedImage} #encodes data as base64
		p = {'format':'json'}
		result = requests.post('https://api.clarifai.com/v1/tag', headers = h, data= d, params = p)
		new_result = json.loads(result.text)
		result_list = new_result['results']
		for each in result_list:
			images_dict[image] = each['result']['tag']['classes']
	return images_dict

#establishes photos that have already been enrolled in Kairos gallery 'celebs':

def original_celebs():
	jb = get_images(facerec_folder)[1:7]
	jt = get_images(facerec_folder)[7:13]
	kk = get_images(facerec_folder)[13:19]
	ts = get_images(facerec_folder)[19:]
	celeb_list = {'justin bieber':jb, 'justin timberlake':jt, 'kim kardashian':kk, 'taylor swift':ts}
	return celeb_list

#enroll photos in album:

def enroll_photos(image, subject_id):
	encodedImage = encode_image(image)
	headers = {'app_id':'0d57f5e2', 'app_key':'39156fbd320d49bdfa17d43db622cb56'}
	data = '{"image":"' + encodedImage + '","gallery_name":"celebs","subject_id":"' + subject_id + '"}'
	response = requests.post('https://api.kairos.com/enroll', headers=headers, data=data)
	result = json.loads(response.text)
	return result

#was used to enroll the original test celebrities:

def enroll_celebs():
	celeb_list = original_celebs()
	for celeb in celeb_list:
		for photo in celeb_list[celeb]:
			enroll_photos(photo, celeb)

#use Kairos to recognize enrolled celebrity in an image:

test_celeb_list = get_images(testimgs_folder)[1:]

def recognize_photos(image):
	encodedImage = encode_image(image)
	headers = {'app_id':'0d57f5e2', 'app_key':'39156fbd320d49bdfa17d43db622cb56'}
	data = '{"image":"' + encodedImage + '","gallery_name":"celebs"}'
	response = requests.post('https://api.kairos.com/recognize', headers=headers, data=data)
	result = json.loads(response.text)
	return result

#create dictionary with image as key and celebrity tag as value:

def celeb_tags(photo_list):
	celeb_dict = {}
	for photo in photo_list:
		match = recognize_photos(photo)
		if 'Errors' in match:
			for codes in match['Errors']:
				if codes['ErrCode'] == 5002:
					print "No faces detected in %s" %photo
		else:
			for each in match['images']:
				y = each['transaction']
				if y['status'] == 'success':
					celeb_dict[photo] = y['subject']
				elif y['message'] == 'No match found':
					user_response = raw_input("Would you like to enroll %s?: " %photo)
					if user_response == 'yes':
						subject_id = raw_input("Who is this? Please enter a name in all lowercase: ")
						enroll_photos(photo, subject_id)
						celeb_dict[photo] = subject_id
					elif user_response == 'no':
						print "Okay, maybe later"
	return celeb_dict

#checks if an image does not have a celebrity tag and enrolls them:
all_images = get_images(facerec_folder) #where enrollment comes from

def new_image_check():
	status = False
	if len(all_images) == 25:
		for image_name in all_images:
			celeb_name = image_name[-3:-1]
			if celeb_name in ['jb', 'jt', 'kk', 'ts']:
				status = True
			elif image_name == 'kairos.py':
				status = True
	elif len(all_images) > 25:
		for image_name in all_images:
			celeb_name = image_name[-3:-1]
			if celeb_name not in ['jb', 'jt', 'kk', 'ts']:
				if image_name != 'kairos.py':
					subject_id = raw_input("Who is this? Please enter a name in all lowercase")
					enroll_photos(image_name, subject_id)
	if status == True:
		print "All photos currently enrolled"


#returns dictionary after checking for new images:

def create_celeb_dict():
	new_image_check()
	x = celeb_tags(test_celeb_list)
	return x

#combines dictionaries created by Clarifai and Kairos

def combine_dict():
	d1 = create_dict()
	d2 = create_celeb_dict()
	if d2 != {}:
		for image in d2:
			if image in d1:
				d1[image].append(d2[image])
			else:
				d1[image] = d2[image]
	return d1

#allows user to input tag for searching

def user_search(searched_tag):
	relevant_imgs = []
	all_images = combine_dict()
	for image_name in all_images:
		if searched_tag in all_images[image_name]:
			relevant_imgs.append(image_name)
	if relevant_imgs != []:
		return relevant_imgs
	else:
		return "Sorry, no photos were found with this tag!"

def main():
	user_input = raw_input("Enter a tag to search: ")
	results = user_search(user_input)
	return results

print main()
