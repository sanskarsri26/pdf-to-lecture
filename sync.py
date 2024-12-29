import subprocess


def pptx_to_pdf(input_file, output_file):
    # Command to convert pptx to pdf using unoconv
    command = ["unoconv", "-f", "pdf", "-o", output_file, input_file]

    try:
        # Execute the command
        subprocess.run(command, check=True)
        print(f"PDF saved at {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")


# Example usage
input_pptx = "Styled_Slides.pptx"
output_pdf = "output.pdf"
pptx_to_pdf(input_pptx, output_pdf)
