import os
from flask import Flask, request, send_file, render_template
from mp_api.client import MPRester
from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import pandas as pd

app = Flask(__name__)

API_KEY = os.getenv("MAPI_KEY")  # Ensure you're using environment variables

@app.route('/')
def index():
    return '''
        <form action="/generate" method="post">
            <label for="material_id">Material ID:</label>
            <input type="text" id="material_id" name="material_id" required>
            <button type="submit">Generate CSV</button>
        </form>
    '''

@app.route('/generate', methods=['POST'])
def generate_csv():
    material_id = request.form.get('material_id')
    if not material_id:
        return "Material ID is required", 400

    try:
        with MPRester(api_key=API_KEY) as mpr:
            structure = mpr.get_structure_by_material_id(material_id)

        material_name = structure.formula.replace(" ", "") + "-" + material_id
        sga = SpacegroupAnalyzer(structure)
        conventional_structure = sga.get_conventional_standard_structure()
        calculator = XRDCalculator(wavelength="CuKa")
        pattern = calculator.get_pattern(conventional_structure)

        # Create CSV
        data = {'2theta': pattern.x, 'Intensity': pattern.y}
        df = pd.DataFrame(data)
        file_path = f"{material_name}.csv"
        df.to_csv(file_path, index=False)

        return send_file(file_path, as_attachment=True, download_name=f"{material_name}.csv")
    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        # Cleanup the file after sending
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render, default to 5000 if not set
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
