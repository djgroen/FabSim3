# colorspep8.py
def colors_16(color_):
    return("\033[2;{num}m {num} \033[0;0m".format(num=str(color_)))


def colors_256(color_):
    num1 = str(color_)
    num2 = str(color_).ljust(3, ' ')
    if color_ % 16 == 0:
        return(f"\033[38;5;{num1}m {num2} \033[0;0m\n")
    else:
        return(f"\033[38;5;{num1}m {num2} \033[0;0m")


print("\nThe 256 colors scheme is:")
print(' '.join([colors_256(x) for x in range(256)]))
