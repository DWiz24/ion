import os
import shutil
import datetime
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = "This command dumps the ion database to a series of fixture files."

    def handle(self, *args, **options):
        fixtures_folder = os.getcwd() + "/fixtures"
        if not os.path.isdir(fixtures_folder):
            print("Script could not find fixtures folder, aborting...")
        models = [x.__module__ + "." + x.__name__ for x in apps.get_models()]
        modellist = []
        for model in models:
            if model.startswith("django"):
                continue
            if not model.startswith(tuple(settings.INSTALLED_APPS)):
                print("Skipping " + model)
                continue
            if not model.startswith("intranet.apps.") or ".models." not in model:
                print("Skipping " + model)
                continue
            modelpath = model[len("intranet.apps."):].replace(".models.", ".")
            modellist.append(modelpath)
        order = depend(set([x.split(".")[0] for x in modellist]))
        order = [x.__module__ + "." + x.__name__ for x in order]
        order = [x[len("intranet.apps."):].replace(".models.", ".") for x in order]
        for modelpath in modellist:
            buf = StringIO()
            call_command("dumpdata", modelpath, stdout=buf)
            buf.seek(0)
            number = order.index(modelpath)
            modelfile = fixtures_folder + "/" + modelpath.split(".")[0] + "/" + str(number).zfill(4) + modelpath.split(".")[1] + ".json"
            modelfilepath = os.path.dirname(modelfile)
            if not os.path.isdir(modelfilepath):
                os.makedirs(modelfilepath)
            with open(modelfile, "w") as f:
                shutil.copyfileobj(buf, f)
            print("Exported " + modelpath)
        readme = open(fixtures_folder + "/README.txt", "w")
        readme.write("These fixtures were exported on %s. To load these fixtures, run the command:\n" % datetime.datetime.now().strftime("%H:%M %m/%d/%Y"))
        readme.write("find ./fixtures/ -name '*.json' -printf '%f %p\\n' | sort | cut -d' ' -f2- | xargs ./manage.py loaddata\n")
        readme.close()


def depend(applist):
    model_deps = []
    for app in applist:
        models = apps.get_app_config(app).get_models()
        for model in models:
            deps = []
            for field in model._meta.fields:
                if hasattr(field.rel, "to"):
                    rel_model = field.rel.to
                    deps.append(rel_model)
            for field in model._meta.many_to_many:
                rel_model = field.rel.to
                if hasattr(rel_model, "natural_key"):
                    deps.append(rel_model)
            model_deps.append((model, deps))
    model_deps.reverse()
    model_list = []
    while model_deps:
        skipped = []
        changed = False
        while model_deps:
            model, deps = model_deps.pop()
            found = True
            for candidate in ((d not in models or d in model_list) for d in deps):
                if not candidate:
                    found = False
            if found:
                model_list.append(model)
                changed = True
            else:
                skipped.append(model)
        if not changed:
            raise CommandError("Failed to resolve dependencies!")
        model_deps = skipped
    return model_list
