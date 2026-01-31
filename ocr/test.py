import easyocr, os, warnings

os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
warnings.filterwarnings("ignore")

reader = easyocr.Reader(['ko','en'], gpu=False)
image_path = "/nfs/img/cd/f6/cdf62bb2ca616f0b49d767473a8289eeddbc88a10e153a851b2de95aec5f5cc3"

results = reader.readtext(image_path)
full_text = " ".join([text for _, text, _ in results])
print(full_text)
