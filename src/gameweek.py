import mongo

def main():
  handler = mongo.Handler()
  handler.update_players()
  handler.update_matches()

if __name__ == "__main__":
  main()