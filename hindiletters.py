import cv2
image = cv2.imread(r'"C:\Users\kanda\Downloads\20251025_204325.jpg"')
cv2.imshow('Image1', image)
cv2.waitKey(0)
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imshow('Gray Image', gray_image)
cv2.waitKey(0)


image2 = cv2.imread(r'"C:\Users\kanda\Downloads\20251025_204251-1761450760714.jpg"')
cv2.imshow('Image2', image2)
cv2.waitKey(0)
gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
cv2.imshow('Gray Image2', gray_image2)
cv2.waitKey(0)

image3 = cv2.imread(r'"C:\Users\kanda\Downloads\20251025_200749.jpg"')
cv2.imshow('Image3', image3)
cv2.waitKey(0)
gray_image3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
cv2.imshow('Gray Image3', gray_image3)
cv2.waitKey(0)

image4 = cv2.imread(r'"C:\Users\kanda\Downloads\20251025_200005.jpg"')
cv2.imshow('Image4', image4)
cv2.waitKey(0)
gray_image4 = cv2.cvtColor(image4, cv2.COLOR_BGR2GRAY)
cv2.imshow('Gray Image4', gray_image4)
cv2.waitKey(0)
