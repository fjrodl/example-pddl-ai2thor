import matplotlib.pyplot as plt

def show_frame(event):
    plt.imshow(event.frame)
    plt.axis('off')
    plt.show()